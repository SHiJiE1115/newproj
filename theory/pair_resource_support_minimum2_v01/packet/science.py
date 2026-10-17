"""Transport definitions; no mathematical result field is selected or dropped."""
import copy
import hashlib
import json
from pathlib import Path

STAGED={
 'data/source1209.json':'iteration449/ORIGINAL_SOURCE1209_FAMILIES_V01.json',
 'data/SYMBOLIC_PROOF_SCOPE_V02.json':'iteration453/SYMBOLIC_PROOF_SCOPE_V02.json',
 'data/SYMBOLIC_SINGLE_PAIR_PROOF_V02.json.gz':'iteration453/SYMBOLIC_SINGLE_PAIR_PROOF_V02.json.gz',
 'data/FROZEN_TWO_PAIR_CANDIDATE_V01.json':'iteration453/FROZEN_TWO_PAIR_CANDIDATE_V01.json',
 'data/PAIR_RESOURCE_MINIMUM_THEOREM_AND_PROOF_V01.txt':'iteration453/PAIR_RESOURCE_MINIMUM_THEOREM_AND_PROOF_V01.txt',
 'original/read_single_pair_proof_v01.py':'iteration453/read_single_pair_proof_v01.py',
 'original/check_two_pair_v01.py':'iteration453/check_two_pair_v01.py',
 'original/separate_two_pair_bayes_v01.py':'iteration453/separate_two_pair_bayes_v01.py',
 'original/derive_pair_resource_result_v01.py':'iteration453/derive_pair_resource_result_v01.py',
 'complete_source.py':'iteration453/complete_source.py',
}
COMPONENTS=[
 {'id':'source_completeness','script':'iteration453/complete_source.py','output':'iteration453/SOURCE_COMPLETENESS_RESULT.json',
  'inputs':['iteration449/ORIGINAL_SOURCE1209_FAMILIES_V01.json']},
 {'id':'single_pair','script':'iteration453/read_single_pair_proof_v01.py','output':'iteration453/SINGLE_PAIR_SEPARATE_READER_RESULT_V01.json',
  'inputs':['iteration453/SYMBOLIC_PROOF_SCOPE_V02.json','iteration449/ORIGINAL_SOURCE1209_FAMILIES_V01.json','iteration453/SYMBOLIC_SINGLE_PAIR_PROOF_V02.json.gz']},
 {'id':'full_class','script':'iteration453/check_two_pair_v01.py','output':'iteration453/TWO_PAIR_FULL_CLASS_RESULT_V01.json',
  'inputs':['iteration453/FROZEN_TWO_PAIR_CANDIDATE_V01.json','iteration449/ORIGINAL_SOURCE1209_FAMILIES_V01.json']},
 {'id':'separate_dp','script':'iteration453/separate_two_pair_bayes_v01.py','output':'iteration453/TWO_PAIR_SEPARATE_DP_RESULT_V01.json',
  'inputs':['iteration453/FROZEN_TWO_PAIR_CANDIDATE_V01.json']},
 {'id':'derived','script':'iteration453/derive_pair_resource_result_v01.py','output':'iteration453/DERIVED_PAIR_RESOURCE_MINIMUM_V01.json',
  'inputs':['iteration453/SINGLE_PAIR_SEPARATE_READER_RESULT_V01.json','iteration453/TWO_PAIR_FULL_CLASS_RESULT_V01.json',
            'iteration453/TWO_PAIR_SEPARATE_DP_RESULT_V01.json','iteration453/PAIR_RESOURCE_MINIMUM_THEOREM_AND_PROOF_V01.txt']},
]


def canonical_bytes(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8')


def science_sha(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def pin(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def check_pin(record,path):
    assert set(record)=={'path','bytes','sha256'}
    assert record==pin(path)


def normalize_all(results,source_path,scope_path,proof_path,frozen_path,theorem_path,result_paths):
    """Every original key and value survives except the specifically validated provenance representation."""
    one=copy.deepcopy(results['single_pair'])
    for key,path,logical in [('source',source_path,'source1209.json'),('scope',scope_path,'SYMBOLIC_PROOF_SCOPE_V02.json'),
                             ('proof',proof_path,'SYMBOLIC_SINGLE_PAIR_PROOF_V02.json.gz')]:
        check_pin(one[key],path)
        one[key]['path']='$INPUT/'+logical
    main=copy.deepcopy(results['full_class'])
    dp=copy.deepcopy(results['separate_dp'])
    assert dp['DP_project_input_read_audit']['unique_read_files']==[str(Path(frozen_path))]
    dp['DP_project_input_read_audit']['unique_read_files']=['$INPUT/FROZEN_TWO_PAIR_CANDIDATE_V01.json']
    derived=copy.deepcopy(results['derived'])
    normal={'single_pair':one,'full_class':main,'separate_dp':dp}
    for key,component in [('one_pair_proof','single_pair'),('two_pair_full_class_proof','full_class'),('two_pair_catalogue_free_DP','separate_dp')]:
        check_pin(derived[key],result_paths[component])
        derived[key]={'logical_component':component,'canonical_science_sha256':science_sha(normal[component])}
    check_pin(derived['theorem_and_proof'],theorem_path)
    derived['theorem_and_proof']['path']='$INPUT/PAIR_RESOURCE_MINIMUM_THEOREM_AND_PROOF_V01.txt'
    normal['derived']=derived
    assert {k:len(v) for k,v in normal.items()}=={k:len(results[k]) for k in normal}
    return normal


def leaf_counts(obj):
    counts={'dicts':0,'lists':0,'integers':0,'booleans':0,'strings':0,'nulls':0,'floats':0}
    def walk(x):
        if isinstance(x,dict):
            counts['dicts']+=1
            for v in x.values():walk(v)
        elif isinstance(x,list):
            counts['lists']+=1
            for v in x:walk(v)
        elif type(x) is bool:counts['booleans']+=1
        elif type(x) is int:counts['integers']+=1
        elif isinstance(x,str):counts['strings']+=1
        elif x is None:counts['nulls']+=1
        elif type(x) is float:counts['floats']+=1
        else:raise TypeError(type(x).__name__)
    walk(obj)
    return counts
