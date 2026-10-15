"""Offline standard-library reproduction of conditional FPR identification."""
import argparse,hashlib,importlib.util,json,os,platform,re,sys,time
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def write(path,x):
 with path.open('x',encoding='utf8') as h:json.dump(x,h,ensure_ascii=False,indent=2,allow_nan=False);h.write('\n');h.flush();os.fsync(h.fileno())
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output-dir',type=Path,required=True)
 p.add_argument('--expect-manifest-sha256',required=True)
 p.add_argument('--execution-kind',choices=['local','github-actions'],default='local')
 p.add_argument('--run-id');p.add_argument('--run-attempt');p.add_argument('--commit')
 args=p.parse_args();assert not args.output_dir.exists(),'Output directory must be new'
 if args.execution_kind=='github-actions':
  assert args.run_id and args.run_id.isdigit() and args.run_attempt and args.run_attempt.isdigit()
  assert args.commit and re.fullmatch('[0-9a-f]{40}',args.commit)
 started=datetime.now(timezone.utc).isoformat();clock=time.perf_counter()
 args.output_dir.mkdir(parents=True)
 receipt={'status':'STARTED','started_utc':started,'execution_kind':args.execution_kind,
  'python_version':platform.python_version(),'platform':platform.platform(),
  'run_id':args.run_id,'run_attempt':args.run_attempt,'commit':args.commit,
  'api_calls':0,'human_gold':False,'scientific_reproduction':False,'actual_dataset_counts':False,
  'scope':'Recompute the MACD four-rounded-point conditional identification calculation from iteration336. Not the PyHealth calculation, an LLM evaluation, or a new underlying paper experiment.'}
 try:
  manifest_raw=(HERE/'MANIFEST.json').read_bytes()
  assert sha(manifest_raw)==args.expect_manifest_sha256,'Manifest pin mismatch'
  manifest=json.loads(manifest_raw);names=set()
  for item in manifest['files']:
   name=item['path'];assert re.fullmatch('[A-Za-z0-9_.-]+',name) and name not in names
   names.add(name);path=HERE/name;assert path.is_file() and not path.is_symlink()
   raw=path.read_bytes();assert len(raw)==item['bytes'] and sha(raw)==item['sha256'],name
  assert {'run.py','exact_bounds.py','inputs.json','expected.json','DERIVATION.json','README.md'}<=names
  inputs=json.loads((HERE/'inputs.json').read_bytes())
  assert inputs['actual_dataset_counts'] is False and inputs['human_gold'] is False
  spec=importlib.util.spec_from_file_location('exact_math',HERE/'exact_bounds.py')
  core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
  computed={'conditional_identification':{},'worlds':{},'same_total_and_prevalence_in_both_worlds':True}
  for name,case in inputs['cases'].items():
   computed['conditional_identification'][name]=core.identify(case['printed_metrics'],case['target_fpr'])
  for world,methods in inputs['constructed_worlds'].items():
   computed['worlds'][world]={}
   for name,counts in methods.items():
    assert all(type(x) is int and x>=0 for x in counts) and len(counts)==4
    tp,fp,fn,tn=counts;total=sum(counts)
    assert total==inputs['constructed_total'] and tp+fn==inputs['constructed_positives'] and fp+tn==inputs['constructed_negatives']
    metrics={'accuracy':F(tp+tn,total),'precision':F(tp,tp+fp),'recall':F(tp,tp+fn),'f1':F(2*tp,2*tp+fp+fn),'fpr':F(fp,fp+tn)}
    printed=inputs['cases'][name]['printed_metrics']
    assert all(F(v)-F(1,200)<metrics[k]<F(v)+F(1,200) for k,v in printed.items())
    computed['worlds'][world][name]={'constructed_counts_TP_FP_FN_TN':counts,'actual_counts':False,
     'total':total,'positives':tp+fn,'negatives':fp+tn,'metrics':{k:core.q(v) for k,v in metrics.items()},
     'strictly_inside_displayed_rounding_intervals':True,'fpr_decimal':float(metrics['fpr'])}
  assert all(computed['worlds']['A'][n]['metrics']['fpr']!=computed['worlds']['B'][n]['metrics']['fpr'] for n in inputs['cases'])
  write(args.output_dir/'computed.json',computed)
  # Load expected only after computing all results; compare full JSON types/values.
  expected=json.loads((HERE/'expected.json').read_bytes())
  matched=canonical(computed)==canonical(expected)
  receipt.update(manifest_sha256=sha(manifest_raw),computed_sha256=sha((args.output_dir/'computed.json').read_bytes()),
   computed_canonical_sha256=sha(canonical(computed).encode('utf8')),full_type_sensitive_expected_match=matched)
  assert matched,'Full calculated result differs from retained reference'
  receipt['status']='PASS_EXACT_CONDITIONAL_REPRODUCTION';code=0
 except Exception as error:
  receipt.update(status='FAIL',error_type=type(error).__name__,error=str(error));code=1
 receipt.update(completed_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-clock,exit_code=code)
 write(args.output_dir/'execution.json',receipt)
 print(json.dumps(receipt,ensure_ascii=False));return code
if __name__=='__main__':raise SystemExit(main())
