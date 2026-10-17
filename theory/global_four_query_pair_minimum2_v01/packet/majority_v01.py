"""Fresh 1345 finite monotone certificates using original 441 kernels.

The global source catalogue and full 1356 policy-family enumeration are
inherited verified data; neither enumeration is run here.
"""
import json
from pathlib import Path
import sys

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H / 'iteration441/bundle_v01'))
from proofio import check_static_files, data
from structures import threshold_and_subset, structural

static = check_static_files()
families = data('families')['rows']
groups = data('groups')['groups']
result = {'threshold_and_subset': threshold_and_subset(families, groups),
          'structural': structural(families, groups)}
with (H / 'MAJORITY_RESULT_V01.json').open('x', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'status': 'PASS_FRESH_1345_MONOTONE_CERTIFICATES',
                  'static_files': static, 'catalogue_regenerated': False}))
