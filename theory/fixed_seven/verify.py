"""Read-only dispatcher for the small fixed-seven cost supplement.

All emits one JSON result after inventory, full frontier/additive and coverage
checks. This is not the six-query classification or an automated proof of the
general submodular theorem; that theorem has its own short written proof.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import subprocess
import time

ROOT=Path(__file__).resolve().parent
ADAPTIVE=[[3,5],[11,28,57,105,120],[11,57,60,105],[19,20],[28,43,57,120],[35,49,52],[67,84,113]]
PRIORITY=[[3,5],[11,28,121],[11,57,60,105],[19,20],[35,49,52],[67,84,113]]
FRONTIERS_SHA='03f29180ea65939b1861661cd3b965bfccc81252e932fe3e76f18032e432cb0c'

def require(ok, message):
    if not ok:raise ValueError(message)

def decode(raw):
    def unique(items):
        value={}
        for k,v in items:
            require(k not in value,'Duplicate JSON key')
            value[k]=v
        return value
    return json.loads(raw,object_pairs_hook=unique,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+x)))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def inventory():
    manifest=decode((ROOT/'MANIFEST.json').read_bytes())
    names=[];size=0
    for row in manifest['files']:
        rel=PurePosixPath(row['path'])
        require(not rel.is_absolute() and '..' not in rel.parts and ':' not in str(rel),'Unsafe manifest path')
        p=(ROOT/rel).resolve()
        require(p.is_relative_to(ROOT),'Manifest escape')
        require(p.is_file() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'Input bytes differ: '+str(rel))
        names.append(str(rel));size+=row['bytes']
    require(len(names)==len(set(names)),'Duplicate file names')
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}
    require(actual==set(names)|{'MANIFEST.json'},'Unlisted or missing files')
    require(sha(ROOT/'seven/ENVELOPE_WITNESSES_V01.json')==FRONTIERS_SHA,'Seven frontier binding')
    require(sha(ROOT/'coverage/data/ENVELOPE_WITNESSES_V01.json')==FRONTIERS_SHA,'Coverage frontier binding')
    return {'files':len(names),'bytes':size,'manifest_sha256':sha(ROOT/'MANIFEST.json')}

def run(relative,seconds):
    command=[sys.executable,'-I','-X','utf8','-B',str(ROOT/relative),'--seconds',str(seconds)]
    child=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=seconds+15)
    require(child.returncode==0,'Child failed: '+relative+'; '+child.stderr.decode('utf8',errors='replace')[:1000])
    result=decode(child.stdout)
    return result

def check_seven(d):
    require(d['status']=='PASS_FIXED_SEVEN_FULL_FRONTIERS_AND_ALL_RATIONAL_CERTIFICATES','Seven status')
    require(d['world_counts']==[8,8] and d['cube_states']==2187,'World/cube completeness')
    require(d['orders_checked']==5040 and d['witness_trees_replayed']==13 and d['LP_certificates_checked']==864,'Incomplete seven layer')
    require(d['adaptive_frontier']==ADAPTIVE and d['priority_frontier']==PRIORITY,'Frontier mismatch')
    require(d['nonnegative_price_ratio_maximum']=='5/4' and d['per_unique_cone_maxima']==['5/4','7/6'],'Additive maxima')
    require(d['order_frontier_sequence_sha256']=='0a6b30e6105264797ff82bf2cbb718a55215cd0f4b6e92c466bfe19df107044b','Order trace')
    require(d['files_written']==0 and d['API_calls']==0,'Unexpected writes/API')
    require(d['six_query_minimality_verified'] is False,'Seven scope overclaim')

def check_coverage(d):
    require(d['status']=='PASS_ALL_864_EXACT_COVERAGE_LPS_AND_MANUAL_RATIO','Coverage status')
    require(d['records_verified']==864 and d['branch_counts']==[432,432],'Incomplete coverage layer')
    require(d['exact_maxima']==['4/3','4/3'],'Coverage maxima')
    require(len(d['controls'])==12,'Missing original positive/negative controls')
    require(d['hand_witness']['AD']=='3' and d['hand_witness']['P']=='4','Manual coverage witness')
    require(d['input_bindings']['frontiers']['sha256']==FRONTIERS_SHA,'Coverage source binding')
    require(d['input_bindings']['certificate']['sha256']=='95cb3a19aee9584301b02ddda2ab57f0d21c0edec7858be72e64a75f08d9f07a','Coverage certificate binding')
    require(d['branches_event_sha256']=='9cd0577e6d5694f0f5fef39ba6c8a8e789173d0ab872b98c3e151f8f52c4ffd4','Coverage exact event trace')
    require(d['inherited_complete_frontiers_not_recomputed'] is True,'Coverage-only scope')
    require(d['general_submodular_upper_bound'] is False,'Coverage is not all submodular')
    require(d['writes_result_files'] is False and d['writes_bytecode'] is False and d['API_calls']==0,'Unexpected writes/API')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['files','seven','coverage','all'],default='all')
    parser.add_argument('--seconds',type=float,default=120.0,help='per mathematical child cooperative cap')
    args=parser.parse_args();started=time.monotonic()
    require(sys.version_info>=(3,10),'Python3.10+ required')
    require(not sys.flags.optimize,'Do not run with -O or -OO')
    require(math.isfinite(args.seconds) and 0<args.seconds<=3600,'Invalid seconds')
    info=inventory(); results={}
    if args.mode in ('seven','all'):
        results['seven']=run('seven/reproduce_seven.py',args.seconds);check_seven(results['seven'])
    if args.mode in ('coverage','all'):
        results['coverage']=run('coverage/check_coverage.py',args.seconds);check_coverage(results['coverage'])
    output={'schema':1,'status':'PASS_FIXED_SEVEN_SUPPLEMENT_'+args.mode.upper(),
        'mode':args.mode,'inventory':info,'results':results,
        'complete_fixed_source_frontiers_rebuilt':args.mode in ('seven','all'),
        'coverage_certificates_reverified':args.mode in ('coverage','all'),
        'coverage_frontier_premise_rebuilt_in_same_invocation':args.mode=='all',
        'all_submodular_upper_bound_mechanically_proved':False,
        'six_query_boundary_reverified':False,'literature_priority_established':False,
        'scope':'Fixed seven source only; general submodular theorem additionally uses the written three-inequality proof.',
        'new_independent_implementation':False,'API_calls':0,'files_written':0,
        'elapsed_seconds':time.monotonic()-started}
    print(json.dumps(output,separators=(',',':')))
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print(json.dumps({'status':'FAIL_OR_INCOMPLETE_FIXED_SEVEN_SUPPLEMENT',
                          'error':type(exc).__name__+': '+str(exc)}),flush=True)
        sys.exit(2)
