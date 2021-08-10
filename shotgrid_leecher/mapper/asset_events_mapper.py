from typing import Dict, Any

from dacite import from_dict
from toolz import get_in, curry

from shotgrid_leecher.record.enums import EventTypes, EventStatuses
from shotgrid_leecher.record.event_status import EventStatus
from shotgrid_leecher.record.new_asset_event import NewAssetEvent
from shotgrid_leecher.record.new_event_commands import NewEventCommand
from shotgrid_leecher.record.shotgrid_project import ShotgridProject
from shotgrid_leecher.record.shotgrid_user import ShotgridUser


def shotgrid_user_from_dict(dic: Dict[str, Any]) -> ShotgridUser:
    return from_dict(ShotgridUser, dic)


def shotgrid_project_from_dict(dic: Dict[str, Any]) -> ShotgridProject:
    return from_dict(ShotgridProject, dic)


def new_asset_event_from_dict(dic: Dict[str, Any]) -> NewAssetEvent:
    project = shotgrid_project_from_dict(dic.get("project"))
    user = shotgrid_user_from_dict(dic.get("user"))
    return NewAssetEvent(
        int(get_in(["entity", "id"], dic)),
        get_in(["entity", "name"], dic),
        dic.get("created_at"),
        user,
        project,
    )


@curry
def new_event_command_from_event(
    event_type: EventTypes, event_status: EventStatuses, event: NewAssetEvent
) -> NewEventCommand:
    return NewEventCommand(
        event.get_unique_id(),
        event_type.value,
        event_status.value,
        event,
    )


def event_status_from_dict(dic: Dict[str, Any]) -> EventStatus:
    return EventStatus(
        dic.get("_id", dic.get("id")),
        dic.get("last_processed_event_id"),
    )
