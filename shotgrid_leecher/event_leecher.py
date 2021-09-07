from shotgrid_leecher.repository import shotgrid_hierarchy_repo
from shotgrid_leecher.utils.connectivity import get_shotgrid_client


def get_recent_events() -> None:
    # save_new_asset_events(None)
    # print(
    #     asset_events_repo.get_last_created_event_id(ShotgridEvents.NEW_ASSET)
    # )
    # print(await asset_events_repo.get_newest_created_asset_id())
    shotgrid = get_shotgrid_client()
    filters = [
        ["id", "greater_than", 100],
        ["event_type", "is", "Shotgun_Asset_New"],
    ]
    fields = [
        "id",
        "event_type",
        "attribute_name",
        "meta",
        "entity",
        "user",
        "project",
        "session_uuid",
        "created_at",
    ]
    order = [{"column": "id", "direction": "asc"}]
    events = shotgrid.find(
        "EventLogEntry",
        filters,
        fields,
        order,
        limit=100,
    )
    proj = shotgrid.find_one(
        "Project",
        [["id", "is", 111]],
        # [["project", "is", {"type": "Project", "id": 87}]],
        fields,
    )
    project_rows = shotgrid_hierarchy_repo.get_hierarchy_by_project(
        209, get_shotgrid_client()
    )
    # response = shotgrid.nav_expand("/Project/87")
    print(proj)
    print(events)
    print(project_rows)
    pass
