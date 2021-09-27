from dataclasses import dataclass

from shotgrid_leecher.record.shotgrid_structures import ShotgridCredentials
from shotgrid_leecher.record.shotgrid_subtypes import FieldsMapping


@dataclass(frozen=True)
class ShotgridToAvalonBatchCommand:
    project_id: int
    project_name: str
    overwrite: bool
    credentials: ShotgridCredentials
    fields_mapping: FieldsMapping


@dataclass(frozen=True)
class ShotgridCheckCommand:
    project_name: str
    project_id: int
    credentials: ShotgridCredentials
