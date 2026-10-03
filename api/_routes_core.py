"""ContentGremlin legacy API routes (reassembled from parts)."""
import base64
from api._routes_parts.part_0 import B64 as B0
from api._routes_parts.part_1 import B64 as B1
from api._routes_parts.part_2 import B64 as B2
from api._routes_parts.part_3 import B64 as B3
from api._routes_parts.part_4 import B64 as B4

_src = base64.b64decode("".join([B0, B1, B2, B3, B4])).decode("utf-8")
_ns = {"__name__": "api._routes_core"}
exec(compile(_src, "api/_routes_core.py", "exec"), _ns)
router = _ns["router"]
