"""Refresh candidate documentation manifests only; private source is read-only.

Usage: python -B tools/public_release/finalize_manifests.py SOURCE_CHECKOUT
No Git writes, network access or experiment execution.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
HEAD='4488906f2ede5312da761766c6177cadc9f3c6de'


def sha(data):return hashlib.sha256(data).hexdigest()


def dump(rel,obj):
    (ROOT/rel).write_text(json.dumps(obj,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')


def main():
    src=Path(sys.argv[1]).resolve()
    assert src!=ROOT and not (ROOT/'.git').exists()
    def git(*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(src),*args])
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    assert not git('status','--porcelain')
    original=git('ls-files','-z').decode().split('\0')[:-1]
    assert len(original)==892
    for rel in original:
        assert (ROOT/rel).is_file(),rel
        if Path(rel).suffix in ('.py','.ipynb','.mjs','.sh'):
            assert (ROOT/rel).read_bytes()==(src/rel).read_bytes(),rel
    # Every existing provenance origin is retained; only current artifact fields change.
    rel='manifests/source_provenance.public.json'
    records=json.loads((src/rel).read_bytes())
    for record in records:
        path=record['path'];target=ROOT/path
        if not target.is_file():continue
        before=(src/path).read_bytes();after=target.read_bytes()
        if before!=after:
            record['sha256']=sha(after);record['size']=len(after)
            record['verification_level']='PUBLIC_DERIVATIVE_WITH_ORIGINAL_AND_FINAL_SHA256'
            record.setdefault('changes',[]).append(dict(phase='4B-4C',before_sha256=sha(before),after_sha256=sha(after),change='Public portfolio documentation/diagnostic derivative; no experiment logic change. Phase 4C transition ledger separately records changes from the preserved candidate.'))
    dump(rel,records)
    # Explicit current scope alongside the earlier third-party review.
    license_review=json.loads((src/'manifests/license_review.public.json').read_bytes())
    license_review['public_release_review']={
        'transformers_diagnostic_source_dumps':'Removed; versions, locations, hashes and upstream references retained.',
        'project_license':'MIT approved in principle for eligible project code; copyright holder/year and exact rights scope pending. No final grant.',
        'full_per_file_inventory':'manifests/license_inventory.public.json',
        'rights_status':'Owner confirmation required before publication.'}
    dump('manifests/license_review.public.json',license_review)
    # Reserve generated report paths before enumerating complete per-file license scope.
    generated=['manifests/license_inventory.public.json','manifests/public_release_provenance.json','manifests/file_inventory.public.json','SHA256SUMS.public.txt']
    paths=sorted({p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}|set(generated))
    licenses=[]
    for path in paths:
        if path.startswith('RAG/results/phase3_e9_claim_verification/factcg_gpu/upstream/'):
            category='FactCG';license_id='MIT';status='NOTICE_RETAINED';notice='RAG/results/phase3_e9_claim_verification/factcg_gpu/upstream/LICENSE'
        elif path=='RAG/results/phase3_e9_claim_verification/factcg_gpu/factcg_backend.py':
            category='Project adapter derived from FactCG semantics';license_id='MIT for upstream portions; project portions pending approval';status='UPSTREAM_NOTICE_RETAINED_PROJECT_RIGHTS_PENDING';notice='RAG/results/phase3_e9_claim_verification/factcg_gpu/upstream/LICENSE'
        elif path.startswith('RAG/results/rag_e6_v4/packages/'):
            category='BERTScore';license_id='MIT';status='NOTICE_RETAINED';notice='RAG/results/rag_e6_v4/packages/LICENSE.bert_score'
        else:
            category='Project-origin source/research record or release documentation';license_id=None;status='OWNER_RIGHTS_AND_LICENSE_SCOPE_CONFIRMATION_REQUIRED';notice=None
        licenses.append(dict(path=path,component=category,license=license_id,status=status,notice=notice))
    dump('manifests/license_inventory.public.json',dict(schema='shroom.public-license-inventory.v1',
        files=licenses,project_license_granted=False,
        blockers=['Confirm rights and MIT scope for project-origin material; approve copyright holder/year.'],
        exclusions=['External datasets','External model weights','External dependency environments'],
        note='File-level categories describe evidence, not a legal conclusion of ownership. Imports alone are not bundled dependencies.'))
    # Every inherited file has before/after hashes; the inventory is a separately verified generated layer.
    changed=[];unchanged=[]
    for path in original:
        if path=='manifests/file_inventory.public.json':continue
        before=(src/path).read_bytes();after=(ROOT/path).read_bytes()
        entry=dict(path=path,original_sha256=sha(before),candidate_sha256=sha(after),size=len(after),decision='BYTE_PRESERVING' if before==after else 'PUBLIC_SAFE_DERIVATIVE')
        (unchanged if before==after else changed).append(entry)
    dump('manifests/public_release_provenance.json',dict(schema='shroom.public-release-provenance.v1',source_commit=HEAD,
        inherited_file_count=892,byte_preserving=unchanged,modified=changed,
        inventory_derivative=dict(path='manifests/file_inventory.public.json',original_sha256=sha((src/'manifests/file_inventory.public.json').read_bytes()),candidate_sha256_location='SHA256SUMS.public.txt',reason='Generated after this provenance layer to avoid circular hashes.'),
        added_paths=[x for x in paths if x not in original],excluded_source_files=[],
        omitted_non_source_material=['.git administration, old history, tags and identities','Private bundles, datasets, weights and runtime caches outside the selected Git tree'],
        significant_source_omissions=0))
    inventory=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(ROOT).as_posix()
        if rel in ('manifests/file_inventory.public.json','SHA256SUMS.public.txt'):continue
        b=p.read_bytes();inventory.append(dict(path=rel,size=len(b),sha256=sha(b)))
    dump('manifests/file_inventory.public.json',dict(schema='shroom.public-release-inventory.v1',files=inventory,
        coverage='All payload files except this inventory and its detached checksum list; SHA256SUMS covers this inventory.',
        excluded_from_recursive_hashing=['manifests/file_inventory.public.json','SHA256SUMS.public.txt']))
    sums=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and p.name!='SHA256SUMS.public.txt':sums.append(sha(p.read_bytes())+'  '+p.relative_to(ROOT).as_posix())
    (ROOT/'SHA256SUMS.public.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
    allfiles=[p for p in ROOT.rglob('*') if p.is_file()]
    print(json.dumps(dict(files=len(allfiles),bytes=sum(p.stat().st_size for p in allfiles),
        byte_preserving=len(unchanged),modified=len(changed)+1,added=len(allfiles)-892,
        modified_paths=[x['path'] for x in changed]+['manifests/file_inventory.public.json'],
        checksum_list_sha256=sha((ROOT/'SHA256SUMS.public.txt').read_bytes()))))


if __name__=='__main__':main()
