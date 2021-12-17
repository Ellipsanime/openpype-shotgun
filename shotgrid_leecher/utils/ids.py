from typing import Any

from bson import ObjectId

_OBJ_ID_LEN = 12


def to_object_id(id_: Any) -> ObjectId:
    return ObjectId(str(id_).zfill(_OBJ_ID_LEN)[:_OBJ_ID_LEN].encode("utf-8"))