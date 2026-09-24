#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -c "
from pathlib import Path
import gzip, base64
src = Path('server.monolith.js').read_bytes()
b64 = base64.b64encode(gzip.compress(src, 9)).decode()
out = Path('payload'); out.mkdir(exist_ok=True)
[p.unlink() for p in out.glob('*.b64')]
CHUNK=500
parts=[b64[i:i+CHUNK] for i in range(0,len(b64),CHUNK)]
[(out/f'{i:02d}.b64').write_text(p) for i,p in enumerate(parts)]
print(f'packed {len(parts)} parts src={len(src)}')
"
