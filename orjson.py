import json
from typing import Any, Optional, Callable, Union

def dumps(obj: Any, default: Optional[Callable[[Any], Any]] = None, option: int = 0, **kwargs) -> bytes:
    def internal_default(o):
        if hasattr(o, 'isoformat'):
            return o.isoformat()
        if default:
            return default(o)
        return str(o)
    return json.dumps(obj, default=internal_default).encode('utf-8')

def loads(obj: Union[str, bytes, bytearray], **kwargs) -> Any:
    return json.loads(obj)

OPT_SERIALIZE_DATACLASS = 1
OPT_SERIALIZE_NUMPY = 2
OPT_INDENT_2 = 4
OPT_SORT_KEYS = 8
OPT_NON_STR_KEYS = 16
OPT_UTC_Z = 32
OPT_PASSTHROUGH_DATETIME = 64
OPT_PASSTHROUGH_DATACLASS = 128
OPT_NAIVE_UTC = 256
OPT_OMIT_MICROSECONDS = 512
OPT_SERIALIZE_UUID = 1024
OPT_STRICT_INTEGER = 2048
OPT_PASSTHROUGH_SUBCLASS = 4096
