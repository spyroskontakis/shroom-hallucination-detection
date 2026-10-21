"""Offline tests: no credentials or network are needed."""
import copy
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock,patch
import run_azure_alternate_rescue as a
import test_e11c as fixtures


class AzureAlternateTests(unittest.TestCase):
    def test_environment_strict(self):
        env={'AZURE_OPENAI_API_KEY':'offline-test-placeholder',
             'AZURE_OPENAI_BASE_URL':a.BASE_URL,'AZURE_OPENAI_DEPLOYMENT':a.MODEL}
        with patch.dict(os.environ,env,clear=True):a.environment()
        for field in env:
            bad=dict(env);del bad[field]
            with patch.dict(os.environ,bad,clear=True),self.assertRaises(ValueError):a.environment()
        for field in ('AZURE_OPENAI_BASE_URL','AZURE_OPENAI_DEPLOYMENT'):
            bad={**env,field:'wrong'}
            with patch.dict(os.environ,bad,clear=True),self.assertRaises(ValueError):a.environment()

    def test_real_frozen_reconciliation(self):
        pending,requests=a.closure.reconcile_local()
        self.assertEqual({r['sample_key'] for r in pending},set(a.IDS))
        self.assertEqual({r['task'] for r in pending},{'PG'})
        for original in requests:
            before=copy.deepcopy(original)
            body=a.rescue_body(original)
            self.assertEqual({k for k in body if body[k]!=original['body'][k]},{'model'})
            self.assertEqual(body['reasoning'],{'effort':'medium'})
            self.assertEqual(original,before)

    def test_dry_run_no_client_or_files(self):
        fake=types.SimpleNamespace(OpenAI=Mock(side_effect=AssertionError('client forbidden')))
        with patch.dict(sys.modules,{'openai':fake}),patch.object(a,'preflight',return_value=([],{})),\
             patch.object(a,'verify_preservation'),patch.object(a.c,'save',side_effect=AssertionError('write forbidden')):
            a.main(['--dry-run'])
        fake.OpenAI.assert_not_called()

    def test_labels_terminal_and_wrong_model_rejected(self):
        for label in a.c.LABELS:
            body=fixtures.response('fixture',label)['response']['body'];body['model']='gpt-5-mini-2025-08-07'
            outcome,retry,answer=a.classify(body)
            self.assertEqual(outcome,label);self.assertFalse(retry)
            self.assertEqual(answer['label'],label)
        body['model']='gpt-5.6-sol'
        with self.assertRaises(ValueError):a.classify(body)

    def test_cached_uncertain_never_resent_and_intent_blocks(self):
        key=a.IDS[0];spec=a.closure.p.pilot.protocol()
        row=next(r for r in a.c.load_candidates() if r['sample_key']==key)
        request=a.c.request(row,spec,2)
        raw=fixtures.response('fixture','uncertain')['response']['body'];raw['model']='gpt-5-mini'
        fake=types.SimpleNamespace(APIStatusError=type('StatusError',(Exception,),{}),
                                   APIConnectionError=type('ConnectionError',(Exception,),{}))
        client=Mock();client.responses.create.return_value.model_dump.return_value=raw
        with tempfile.TemporaryDirectory(dir=a.c.PRIVATE) as temp,patch.object(a,'OUT',a.c.Path(temp)),\
             patch.dict(sys.modules,{'openai':fake}):
            first=a.run_candidate(client,key,request,spec)
            second=a.run_candidate(client,key,request,spec)
            self.assertEqual(first,second);self.assertEqual(first['label'],'uncertain')
            self.assertTrue(first['excluded_from_original_supervision'])
            self.assertEqual(client.responses.create.call_count,1)
        with tempfile.TemporaryDirectory(dir=a.c.PRIVATE) as temp,patch.object(a,'OUT',a.c.Path(temp)):
            a.c.save(a.OUT/key/'intent_1.json',{})
            with self.assertRaises(ValueError):a.run_candidate(client,key,request,spec)

    def test_schema_failure_retries_only_to_cap(self):
        key=a.IDS[0];spec=a.closure.p.pilot.protocol()
        row=next(r for r in a.c.load_candidates() if r['sample_key']==key)
        request=a.c.request(row,spec,2)
        raw=fixtures.response('fixture')['response']['body'];raw['model']='gpt-5-mini'
        raw['output'][0]['content'][0]['text']='{}'
        fake=types.SimpleNamespace(APIStatusError=type('StatusError',(Exception,),{}),
                                  APIConnectionError=type('ConnectionError',(Exception,),{}))
        client=Mock();client.responses.create.return_value.model_dump.return_value=raw
        with tempfile.TemporaryDirectory(dir=a.c.PRIVATE) as temp,patch.object(a,'OUT',a.c.Path(temp)),\
             patch.dict(sys.modules,{'openai':fake}),patch.object(a.time,'sleep'):
            result=a.run_candidate(client,key,request,spec)
            self.assertIsNone(result['label']);self.assertEqual(result['outcome'],'invalid_schema')
            self.assertEqual(client.responses.create.call_count,3)


if __name__=='__main__':unittest.main()
