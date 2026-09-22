#!/bin/bash
set -u
cd /home/study/jev-guided-decoding
export PATH=/home/study/.local/bin:$PATH
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
uv run --no-sync python -u - <<'PY' > results/boundary-study.log 2>&1
import sys,torch,runpy,json,platform
from datetime import datetime,timezone
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
with open('results/boundary-execution.json','x') as f:
 json.dump({'at':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'intraop_threads':torch.get_num_threads(),'interop_threads':torch.get_num_interop_threads()},f)
sys.argv=['study.py','run','--manifest','research/protocols/boundary-attention-v1','--output','results/boundary-attention-v1','--device','cuda','--local-files-only','--key-file','/home/study/.typesafe.ai/jev']
runpy.run_path('research/iterations/boundary_attention/study.py',run_name='__main__')
PY
code=$?
printf '%s\n' "$code" > results/boundary-exit-code.txt
exit "$code"
