#!/bin/bash
set -eu
cd /home/study/jev-guided-decoding
mkdir -p results
trap 'echo $? > results/selective-exit-code.txt' EXIT
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
.venv/bin/python - <<'INNER'
import runpy,sys,torch,json,subprocess
from pathlib import Path
Path('results/selective-execution.json').write_text(json.dumps({'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],text=True),'threads':1,'interop_threads':1}))
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
sys.argv=['study.py','run','--manifest','research/protocols/selective-attention-v1','--output','results/selective-attention-v1','--device','cuda','--local-files-only']
runpy.run_path('research/iterations/selective_attention/study.py',run_name='__main__')
INNER
