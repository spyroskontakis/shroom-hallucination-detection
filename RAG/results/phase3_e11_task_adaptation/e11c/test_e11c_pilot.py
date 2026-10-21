import unittest
import tempfile
from contextlib import ExitStack, nullcontext
from unittest.mock import patch
import e11c_common as c
import e11c_pilot as p


class PilotTests(unittest.TestCase):
    def test_selection_and_frozen_request_equality(self):
        rows=p.candidates()
        full={r['custom_id']:r for r in c.read_rows(c.PRIVATE/'round_1/requests.jsonl')}
        reqs=c.read_rows(p.PILOT/'round_1/requests.jsonl')
        self.assertEqual(len(rows),300)
        self.assertEqual(len(reqs),300)
        self.assertEqual(reqs,[full[r['custom_id']] for r in reqs])

    def test_scope_restores_on_failure(self):
        old=p.batch.PRIVATE
        with self.assertRaises(RuntimeError):
            with p.scope():
                self.assertEqual(p.batch.PRIVATE,p.PILOT)
                self.assertEqual(len(p.batch.load_candidates()),300)
                raise RuntimeError('fixture')
        self.assertEqual(p.batch.PRIVATE,old)

    def test_pilot_shard_and_no_full_shard(self):
        with p.scope():
            _,path=p.batch.checked_shard(1,1)
            self.assertEqual(path,p.PILOT/'round_1/batch_001.jsonl')
            with self.assertRaises(ValueError): p.batch.checked_shard(1,2)

    def test_api_guard_before_network(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')):
            with self.assertRaises(ValueError): p.run_action('submit',1,False)
            with self.assertRaises(ValueError): p.run_action('download',1,False)

    def test_wrong_protocol_fails(self):
        spec={**p.protocol(),'protocol_sha256':'bad'}
        with patch.object(c,'load_protocol',return_value=spec):
            with self.assertRaises(ValueError): p.protocol()

    def test_audit_usage_cost_and_uncertain_provenance(self):
        from test_e11c import sample,response
        spec=p.protocol()
        with tempfile.TemporaryDirectory() as temp, ExitStack() as stack:
            home=c.Path(temp); private=home/'private/pilot_300'
            folder=private/'round_1'; state=folder/'batch_001'
            rows=[sample(i,tuple(c.POLICY)[i//100]) for i in range(300)]
            raw=[]; ledger=[]; reqs=[]
            for i,row in enumerate(rows):
                cid='fixture_'+str(i); label=c.LABELS[i%3]
                reqs.append({'custom_id':cid})
                item=response(cid,label)
                item['response']['body']['usage']={'input_tokens':100,'output_tokens':200,
                    'output_tokens_details':{'reasoning_tokens':150},'input_tokens_details':{'cached_tokens':0}}
                raw.append(item)
                ledger.append({'sample_key':row['sample_key'],'task':row['task'],'outcome':label,
                    'accepted':label!='uncertain','synthetic':{},'history':[{'outcome':label,
                    'raw_response_path':'private/pilot_300/round_1/batch_001/output_file.jsonl',
                    'raw_response_line':i+1}]})
            c.write_once(folder/'requests.jsonl',c.rows_bytes(reqs))
            c.write_once(state/'output_file.jsonl',c.rows_bytes(raw))
            c.save(state/'download_receipt.json',{'batch':{'status':'completed'},
                'files':[{'path':'output_file.jsonl'}]})
            c.write_once(private/'candidates.jsonl',c.rows_bytes(rows))
            manifest=home/'selection.json';c.save(manifest,{})
            for obj,name,value in [(c,'HERE',home),(p,'PILOT',private),(p,'MANIFEST',manifest),
                (p,'protocol',lambda:spec),(p,'candidates',lambda:rows),(p,'scope',nullcontext)]:
                stack.enter_context(patch.object(obj,name,value))
            stack.enter_context(patch.object(p.results,'parse_round',return_value=({'retryable':0},ledger)))
            stack.enter_context(patch('builtins.print'))
            p.audit(1)
            audit=c.read_json(home/'E11C_PILOT_AUDIT.json')
            self.assertEqual(audit['status'],'PASS')
            self.assertEqual(audit['input_tokens'],30000)
            self.assertEqual(audit['output_tokens'],60000)
            self.assertEqual(audit['reasoning_tokens'],45000)
            self.assertAlmostEqual(audit['pilot_batch_cost_estimate_usd'],0.66)
            self.assertAlmostEqual(audit['full_12000_batch_extrapolation_usd'],26.4)
            self.assertEqual(audit['labels'],{label:100 for label in c.LABELS})
            labels=c.read_rows(private/'parsed_labels.jsonl')
            self.assertIn('reference_text_sha256',labels[2])


if __name__=='__main__': unittest.main(verbosity=2)
