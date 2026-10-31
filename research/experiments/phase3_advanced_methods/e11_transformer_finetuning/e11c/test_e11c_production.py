"""Production population, preservation and terminal-answer invariants."""
import unittest
from unittest.mock import patch
import e11c_common as c
import e11c_production as p


class ProductionTests(unittest.TestCase):
    def test_partition_and_exact_frozen_requests(self):
        pool, remaining, pilot = p.partition()
        self.assertEqual((len(pool),len(remaining),len(pilot)),(12000,11700,300))
        used={r['sample_key'] for r in pilot}
        self.assertFalse(used & {r['sample_key'] for r in remaining})
        requests=c.read_rows(p.PRIVATE/'round_1/requests.jsonl')
        self.assertEqual(requests,[c.request(r,p.pilot.protocol()) for r in remaining])
        self.assertEqual(len({r['custom_id'] for r in requests}),11700)

    def test_frozen_files_and_private_ignore(self):
        p.preservation()
        p.ignored()
        self.assertEqual(p.pilot.protocol()['protocol_sha256'],p.pilot.EXPECTED)

    def test_pilot_uncertain_terminal_and_binary_exclusion(self):
        _,_,ledger=p.partition()
        self.assertTrue(all(r['outcome'] in c.LABELS and not r['retryable'] for r in ledger))
        binary=[r for r in ledger if r['accepted']]
        self.assertEqual(len(binary),298)
        self.assertTrue(all(r['outcome'] in c.LABELS[:2] for r in binary))
        # On final audit, exercise the actual consolidated export as well.
        path=p.PRIVATE/'full_audit_ledger.jsonl'
        if path.exists():
            full=c.read_rows(path)
            labels=c.read_rows(p.PRIVATE/'parsed_labels.jsonl')
            exported=c.read_rows(p.PRIVATE/'future_binary_supervision.jsonl')
            self.assertEqual(len(full),12000)
            self.assertEqual(len({r['sample_key'] for r in full}),12000)
            self.assertFalse(any(r['retryable'] for r in full if r['outcome'] in c.LABELS))
            self.assertTrue(all(r['label'] in c.LABELS for r in labels))
            self.assertEqual(exported,[r['synthetic'] for r in full if r['accepted']])
            self.assertTrue(all(r['llm_label'] in c.LABELS[:2] for r in exported))
            for row in full:
                terminal=[h for h in row['history'] if h['outcome'] in c.LABELS]
                self.assertLessEqual(len(terminal),1)
                if terminal:
                    self.assertEqual(terminal[0],row['history'][-1])

    def test_scoped_population_and_api_guard(self):
        old=p.pilot.batch.PRIVATE
        with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')):
            with p.scope():
                self.assertEqual(len(p.pilot.batch.load_candidates()),11700)
                with self.assertRaises(ValueError): p.pilot.batch.submit(1,1,False)
        self.assertEqual(p.pilot.batch.PRIVATE,old)


if __name__=='__main__': unittest.main()
