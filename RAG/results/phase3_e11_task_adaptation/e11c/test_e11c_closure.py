"""Closure identity and prior-answer preservation checks."""
import unittest
import e11c_common as c
import close_e11c_retry as r


class ClosureTests(unittest.TestCase):
    def test_only_four_pg_requests_with_unchanged_bodies(self):
        with r.p.scope():
            report,ledger=r.p.pilot.results.parse_round(1,write=False)
            _,path=r.p.pilot.batch.checked_shard(2,1)
        pending=[x for x in ledger if x['retryable']]
        self.assertEqual(len(pending),4)
        self.assertEqual({x['task'] for x in pending},{'PG'})
        requests=c.read_rows(path)
        ids={x['sample_key'] for x in pending}
        rows=[x for x in r.p.candidates() if x['sample_key'] in ids]
        self.assertEqual(requests,[c.request(x,r.p.pilot.protocol(),2) for x in rows])
        prior={x['sample_key']:x for x in ledger}
        for x in rows:
            self.assertEqual(prior[x['sample_key']]['outcome'],'http_429')

    def test_previous_answers_unchanged_in_closed_export(self):
        path=r.p.PRIVATE/'closed/full_audit_ledger.jsonl'
        if not path.exists():return
        old=c.read_rows(r.p.PRIVATE/'full_audit_ledger.jsonl');new=c.read_rows(path)
        self.assertEqual(len(new),12000)
        self.assertEqual(len({x['sample_key'] for x in new}),12000)
        self.assertEqual({x['sample_key'] for x,y in zip(old,new) if x!=y},
                         {x['sample_key'] for x in old if x['retryable']})
        self.assertTrue(all(x['outcome'] in c.LABELS and not x['retryable'] for x in new))
        binary=c.read_rows(r.p.PRIVATE/'closed/future_binary_supervision.jsonl')
        self.assertEqual(binary,[x['synthetic'] for x in new if x['accepted']])
        self.assertTrue(all(x['llm_label'] in c.LABELS[:2] for x in binary))


if __name__=='__main__':unittest.main()
