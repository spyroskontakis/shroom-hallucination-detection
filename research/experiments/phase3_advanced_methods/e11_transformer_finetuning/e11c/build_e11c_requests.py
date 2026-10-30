"""Build frozen Batch JSONL locally; retries require a complete prior-round report."""
import argparse
from e11c_common import *


def build(attempt=1):
    spec = load_protocol()
    candidates = load_candidates()
    if attempt > 1:
        from parse_e11c_results import parse_round
        report, ledger = parse_round(attempt-1, write=False)
        wanted = {r['sample_key'] for r in ledger if r['retryable']}
        candidates = [r for r in candidates if r['sample_key'] in wanted]
    requests = [request(r,spec,attempt) for r in candidates]
    folder = PRIVATE / f'round_{attempt}'
    write_once(folder/'requests.jsonl',rows_bytes(requests))
    shards=[]
    for start in range(0,len(requests),500):
        path=folder/f'batch_{start//500+1:03d}.jsonl'
        chunk=requests[start:start+500]
        write_once(path,rows_bytes(chunk))
        require(path.stat().st_size < 200_000_000, 'Batch file limit')
        shards.append({'path':path.name,'sha256':sha(path),'rows':len(chunk),
                       'custom_ids':[r['custom_id'] for r in chunk]})
    manifest={'attempt':attempt,'rows':len(requests),'protocol_sha256':spec['protocol_sha256'],
              'candidate_pool_sha256':spec['candidates']['sha256'],
              'requests_sha256':sha(folder/'requests.jsonl'),'shards':shards}
    save(folder/'request_manifest.json',manifest)
    print('Prepared round',attempt,'requests',len(requests),'shards',len(shards))
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--attempt',type=int,choices=(1,2,3),default=1)
    build(parser.parse_args().attempt)
