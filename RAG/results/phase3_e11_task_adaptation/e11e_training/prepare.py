"""Read-only reconciliation of E11-C/D, then freeze E11-E without model fits."""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
from e11e_common import *


def prepare():
    require(not (HERE/'private/returned').exists(),'already launched; do not prepare again')
    validate_local()
    verify_manifest(C,'E11C_MANIFEST.json');verify_manifest(D,'E11D_MANIFEST.json')
    cp=load_module('e11c_preparation_readonly',C/'prepare_training.py')
    cp.production.preservation()
    for name in ('E11C_PRODUCTION_MANIFEST.json','E11C_ALTERNATE_MODEL_RESCUE_MANIFEST.json'):
        cp.production.check_hashes(cp.c.HERE,cp.c.read_json(cp.c.HERE/name)['files_sha256'])
    cs=read(C/'E11C_TRAINING_PROTOCOL.json');ds=read(D/'E11D_LOSS_PROTOCOL.json');a=load_protocol()
    require(digest(encoded({k:v for k,v in cs.items() if k!='protocol_sha256'}))==cs['protocol_sha256'],'C protocol content hash')
    require(cs['stage2']==a['training'] and cs['model']==a['model'] and cs['input']==a['input'],'C/A inherited settings')
    require(ds['lambda']==.1 and ds['margin']==0 and ds['temperature'] is None,'D objective')
    require((HERE/'contrastive.py').read_bytes()==(D/'contrastive.py').read_bytes(),'exact D implementation')
    pool=cp.c.load_candidates()
    _,_,pilot=cp.production.partition()
    with cp.production.scope(): _,ledger=cp.production.pilot.results.parse_round(1,write=False)
    outcomes=pilot+ledger
    synthetic=[r['synthetic'] for r in outcomes if r['accepted']]
    require(len(synthetic)==len({r['sample_key'] for r in synthetic})==11887,'definitive population')
    require(Counter(r['llm_label'] for r in synthetic)=={'hallucination':5111,'not_hallucination':6776},'teacher labels')
    require(all(r['teacher_model_id']=='gpt-5.6-sol' for r in synthetic),'homogeneous teacher')
    require(sum(r['outcome']=='uncertain' for r in outcomes)==109 and sum(r['retryable'] for r in outcomes)==4,'uncertain and failures')
    labels={r['sample_key']:r for r in synthetic}
    export=cp.production.PRIVATE/'future_binary_supervision.jsonl'
    require(read_jsonl(export)==[labels[r['sample_key']] for r in pool if r['sample_key'] in labels],'authoritative binary export')
    rescue=read_jsonl(cp.c.PRIVATE/'azure_alternate_rescue/rescue_judgments.jsonl')
    require(len(rescue)==4 and not set(labels)&{r['sample_key'] for r in rescue},'four alternate judgments excluded')
    selected=[r for r in pool if r['sample_key'] in labels]
    groups=defaultdict(list)
    for row in selected: groups[cp.c.parts(row['task'],row['reference_text'],row['hyp'])].append(row)
    dedup=[];removed=[];conflicting_groups=0
    for group in groups.values():
        conflict=len({labels[r['sample_key']]['label'] for r in group})>1
        conflicting_groups+=int(conflict)
        dedup.extend([] if conflict else group[:1])
        removed.extend({'sample_key':r['sample_key'],'reason':'conflicting_identical_input' if conflict else 'duplicate_input'} for r in (group if conflict else group[1:]))
    require(cp.c.rows_bytes(removed)==(C/'private/duplicate_exclusions.jsonl').read_bytes(),'identical duplicate/conflict exclusions')
    require(len(removed)==82,'duplicate exclusion count')
    kept_ids={r['sample_key'] for r in dedup};selected=[r for r in selected if r['sample_key'] in kept_ids]
    bases,human,fold_of=baselines()
    synthetic_sizes=[];exclusions=[];all_prepared={}
    for f in range(1,6):
        kept,excluded=cp.purge(selected,[r for sid,r in human.items() if fold_of[sid]==f])
        stage1=[{'sample_id':r['sample_key'],'fold_id':0,'task':r['task'],'reference_field':cp.c.POLICY[r['task']],
                 'text':a['input']['sequence_a_template'].format(task=r['task'],reference=r['reference_text']),
                 'text_pair':a['input']['sequence_b_template'].format(hyp=r['hyp']),'label':labels[r['sample_key']]['label']} for r in kept]
        folder=C/f'private/fold_{f}';meta=cs['folds'][str(f)]
        require(cp.c.rows_bytes(stage1)==(folder/'synthetic.jsonl').read_bytes(),'synthetic replay/order mismatch')
        require(cp.c.rows_bytes(excluded)==(folder/'leakage_exclusions.jsonl').read_bytes(),'validation exclusion mismatch')
        for name,sha in meta['files_sha256'].items():
            require(sha_file(folder/name)==sha,'C prepared file hash')
            write_once(HERE/f'private/fold_{f}'/name,(folder/name).read_bytes())
        for split in ('train','heldout'):
            require((folder/f'{split}.jsonl').read_bytes()==(E11/f'e11a_prepared/fold_{f}/{split}.jsonl').read_bytes(),'human split bytes')
        synthetic_sizes.append(len(stage1));exclusions.append(len(excluded))
        for row in stage1+read_jsonl(folder/'train.jsonl')+read_jsonl(folder/'heldout.jsonl'): all_prepared[row['sample_id']]=row
    require(synthetic_sizes==[11787,11791,11795,11787,11790],'STOP: Stage-1 sizes differ')
    require(exclusions==[18,14,10,18,15],'STOP: validation exclusions differ')
    from transformers import AutoTokenizer
    # Byte-identical loss module from D; explicitly resolve E's local copy.
    contrast=load_module('e11e_frozen_contrastive',HERE/'contrastive.py')
    tokenizer=AutoTokenizer.from_pretrained(str(ROOT/a['model']['local_mirror_dir']),local_files_only=True,use_fast=True)
    prepared=list(all_prepared.values());mask_count=0;minimum=512
    for start in range(0,len(prepared),256):
        rows=prepared[start:start+256]
        tokens=tokenizer([r['text'] for r in rows],[r['text_pair'] for r in rows],add_special_tokens=True,truncation='longest_first',max_length=512,padding=False)
        masks=contrast.sequence_masks(tokens);mask_count+=len(masks);minimum=min(minimum,min(sum(m) for pair in masks for m in pair))
    loss={k:ds[k] for k in ('classification','formula','total_loss','lambda','margin','temperature','normalization','representation','contextualization','positive','negative','rationale')}
    protocol={**cs,'experiment':'E11-E','architecture':'five fold-specific synthetic Stage-1 then human Stage-2 fits, both with frozen E11-D contrastive loss',
              'e11c_protocol_sha256':cs['protocol_sha256'],'e11d_loss_protocol_file_sha256':sha_file(D/'E11D_LOSS_PROTOCOL.json'),
              'contrastive':loss,'contrastive_applies_to_stages':[1,2],
              'runtime_code_sha256':{name:sha_file(HERE/name) for name in ('train_stages.py','contrastive.py')}}
    protocol.pop('protocol_sha256',None);protocol['protocol_sha256']=digest(encoded(protocol))
    save(HERE/'E11E_TRAINING_PROTOCOL.json',protocol)
    save(HERE/'private/PRESERVED_SHA256.json',protected_files())
    checks={'status':'PASS','model_fits':0,'baselines':bases,'synthetic_pool':11887,'teacher_model':'gpt-5.6-sol',
            'uncertain_excluded':109,'Azure_rescue_excluded':4,'duplicate_input_exclusions':82,
            'duplicate_reasons':dict(Counter(r['reason'] for r in removed)),'conflicting_groups':conflicting_groups,
            'synthetic_rows_by_fold':synthetic_sizes,'validation_overlap_exclusions':exclusions,
            'synthetic_export_sha256':sha_file(export),'teacher_protocol_sha256':cs['teacher_protocol_sha256'],
            'synthetic_and_human_prepared_files_identical_to_C':True,'loss_implementation_identical_to_D':True,
            'tokenizer_masks_checked':mask_count,'minimum_retained_sequence_tokens':minimum,
            'folds_sha256':cs['folds_sha256'],'evaluator_sha256':sha_file(E11/'e11a_results/assemble_e11a_results.py'),
            'protocol_sha256':protocol['protocol_sha256'],'official_test_access':False,'teacher_calls':0,
            'leakage_limit':read(C/'PRETRAINING_AUDIT.json')['leakage_limit']}
    save(HERE/'PRETRAINING_CHECKS.json',checks)
    print('PASS: exact C subsets/exclusions and D loss verified; preparation complete; zero fits.')


def freeze():
    require(not (HERE/'private/returned').exists(),'already launched')
    tests=read(HERE/'PRETRAINING_TESTS.json');require(tests['status']=='PASS','pretraining tests')
    checks=read(HERE/'PRETRAINING_CHECKS.json')
    require(protected_files()==read(HERE/'private/PRESERVED_SHA256.json'),'protected artifacts changed')
    audit={**checks,'frozen_utc':datetime.now(timezone.utc).isoformat(),'tests':tests,
           'protected_files':len(read(HERE/'private/PRESERVED_SHA256.json')),
           'preservation_snapshot_sha256':sha_file(HERE/'private/PRESERVED_SHA256.json')}
    save(HERE/'E11E_PRETRAINING_AUDIT.json',audit)
    write_once(HERE/'E11E_PRETRAINING_AUDIT.md',('# E11-E pretraining audit: PASS\n\nExact E11-C prepared bytes replayed from the homogeneous 11,887 gpt-5.6-sol labels. Excluded 109 uncertain, four Azure judgments, and the same 82 duplicate/conflicting rows. Validation exclusions 18/14/10/18/15; synthetic sizes 11,787/11,791/11,795/11,787/11,790. Human folds unchanged.\n\nE11-D cosine loss implementation copied byte for byte: lambda 0.1, margin zero, no temperature, final-layer sequence mean pooling with textual prefixes retained and special/padding tokens excluded. Applied in both stages.\n\nExact C model, tokenizer, 512-token truncation, seed 42, optimizer, class weights, batch/accumulation, BF16, scheduler, one synthetic epoch and five human epochs. Ten fits only. All four baselines recomputed using the authoritative evaluator.\n\nPretraining tests passed. No teacher calls or official-test access. Full provenance, exact loss and settings are in E11E_TRAINING_PROTOCOL.json and the JSON audit.\n').encode())
    manifest={name:sha_file(HERE/name) for name in ('train_stages.py','contrastive.py','E11E_TRAINING_PROTOCOL.json','E11E_PRETRAINING_AUDIT.json','modal_training.py')}
    save(HERE/'RUNTIME_MANIFEST.json',manifest)
    print('PASS: pretraining audit and runtime hashes frozen before any training.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
    freeze() if args.freeze else prepare()
