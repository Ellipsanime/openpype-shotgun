import random
import uuid
from datetime import datetime
from typing import Dict, Any, Callable, List

import pytest
from _pytest.monkeypatch import MonkeyPatch
from assertpy import assert_that
from mock import Mock
from mongomock.mongo_client import MongoClient

from shotgrid_leecher.controller import schedule_controller
from shotgrid_leecher.domain import batch_domain, schedule_domain
from shotgrid_leecher.record.enums import DbName, DbCollection
from shotgrid_leecher.record.http_models import BatchConfig
from shotgrid_leecher.record.results import BatchResult
from shotgrid_leecher.utils import connectivity as conn
from utils.async_mongoclient import AsyncMongoClient

Map = Dict[str, Any]


def _fun(param: Any) -> Callable[[Any], Any]:
    return lambda *_: param


def _all_projects(client: MongoClient) -> List[Map]:
    return list(
        client.get_database(DbName.SCHEDULE.value)
        .get_collection(DbCollection.SCHEDULE_PROJECTS.value)
        .find({})
    )


def _all_logs(client: MongoClient) -> List[Map]:
    return list(
        client.get_database(DbName.SCHEDULE.value)
        .get_collection(DbCollection.SCHEDULE_LOGS.value)
        .find({})
    )


def _rollin_projects(client: MongoClient, n=2):
    batches = [
        _batch_config().to_schedule_command(f"project_{str(uuid.uuid4())[:5]}")
        for _ in range(n)
    ]
    client.get_database(DbName.SCHEDULE.value).get_collection(
        DbCollection.SCHEDULE_PROJECTS.value
    ).insert_many(
        [{"_id": x.project_name, "command": x.to_dict()} for x in batches]
    )
    client.get_database(DbName.SCHEDULE.value).get_collection(
        DbCollection.SCHEDULE_QUEUE.value
    ).insert_many(
        [
            {
                "command": x.to_dict(),
                "created_at": datetime.utcnow(),
            }
            for x in batches
        ]
    )


def _batch_config() -> BatchConfig:
    return BatchConfig(
        shotgrid_project_id=random.randint(10 ** 2, 10 ** 5),
        shotgrid_url=f"http://{uuid.uuid4()}.com",
        script_name=str(uuid.uuid4()),
        script_key=str(uuid.uuid4()),
        fields_mapping={},
    )


@pytest.mark.asyncio
async def test_schedule_batch(monkeypatch: MonkeyPatch):
    # Arrange
    client = AsyncMongoClient(MongoClient())
    project_name = f"project_{str(uuid.uuid4())[:5]}"
    monkeypatch.setattr(conn, "get_db_client", _fun(client.mongo_client))
    monkeypatch.setattr(conn, "get_async_db_client", _fun(client))
    config = _batch_config()
    # Act
    await schedule_controller.schedule_batch(project_name, config)

    # Assert
    assert_that(_all_projects(client.mongo_client)).extracting(
        "_id"
    ).is_equal_to([project_name])
    assert_that(_all_projects(client.mongo_client)).extracting(
        "command"
    ).extracting("project_id").is_equal_to([config.shotgrid_project_id])
    assert_that(_all_projects(client.mongo_client)).extracting(
        "command"
    ).extracting("credentials").extracting("shotgrid_url").is_equal_to(
        [config.shotgrid_url]
    )


@pytest.mark.asyncio
async def test_dequeue_scheduled_batches(monkeypatch: MonkeyPatch):
    # Arrange
    size = 3
    client = AsyncMongoClient(MongoClient())
    batch = Mock(return_value=BatchResult.OK)
    _rollin_projects(client.mongo_client, size)
    monkeypatch.setattr(batch_domain, "update_shotgrid_in_avalon", batch)
    monkeypatch.setattr(conn, "get_async_db_client", _fun(client))
    # Act
    await schedule_domain.dequeue_and_process_batches()

    # Assert
    assert_that(_all_logs(client.mongo_client)).extracting(
        "batch_result"
    ).is_equal_to(
        [BatchResult.OK.value, BatchResult.OK.value, BatchResult.OK.value]
    )


@pytest.mark.asyncio
async def test_dequeue_scheduled_batches_part_success(
    monkeypatch: MonkeyPatch,
):
    # Arrange
    steps = []

    def _batch(_: Any):
        steps.append(1)
        if len(steps) == 1:
            return BatchResult.OK
        if len(steps) == 2:
            raise Exception("WAT!")
        if len(steps) == 3:
            return BatchResult.NO_SHOTGRID_HIERARCHY

    size = 3
    client = AsyncMongoClient(MongoClient())
    _rollin_projects(client.mongo_client, size)
    monkeypatch.setattr(batch_domain, "update_shotgrid_in_avalon", _batch)
    monkeypatch.setattr(conn, "get_async_db_client", _fun(client))
    # Act
    await schedule_domain.dequeue_and_process_batches()

    # Assert
    assert_that(_all_logs(client.mongo_client)).extracting(
        "batch_result"
    ).is_equal_to(
        [
            BatchResult.OK.value,
            BatchResult.FAILURE.value,
            BatchResult.NO_SHOTGRID_HIERARCHY.value,
        ]
    )