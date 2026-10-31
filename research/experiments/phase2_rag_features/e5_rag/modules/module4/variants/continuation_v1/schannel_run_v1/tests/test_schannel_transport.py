import importlib.util,json,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/'scripts'/'module4_schannel_acquire.py';s=importlib.util.spec_from_file_location('schannel',SCRIPT);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_safe_args_and_url_is_single_argument(self):
  with tempfile.TemporaryDirectory() as td:
   url='https://en.wiktionary.org/w/api.php?action=query&titles=a%26b';a=m.curl_args(url,Path(td)/'b',Path(td)/'h');self.assertEqual(a[1],'-q');self.assertEqual(a[-1],url);self.assertNotIn('--insecure',a);self.assertNotIn('-k',a)
 def test_raw_bytes_preserved_by_hash(self):
  raw=b'\x00\xff{"x":1}\r\n';self.assertEqual(m.sha256_bytes(raw),__import__('hashlib').sha256(raw).hexdigest())
 def test_valid_and_api_error_json(self):
  m.validate_json(b'{"query":{"general":{}}}','siteinfo')
  with self.assertRaises(ValueError):m.validate_json(b'{"error":{"code":"x"}}','siteinfo')
 def test_incomplete_or_wrong_structure_rejected(self):
  with self.assertRaises(Exception):m.validate_json(b'{','revision_identity')
  with self.assertRaises(ValueError):m.validate_json(b'{"query":{}}','revision_identity')
 def test_certificate_failure_is_global_baseexception(self):self.assertTrue(issubclass(m.GlobalTLSFailure,BaseException));self.assertFalse(issubclass(m.GlobalTLSFailure,Exception))
 def test_http_failure_is_retryable_but_tls_is_not(self):self.assertIn(22,m.TRANSIENT_EXITS);self.assertNotIn(m.TLS_EXIT,m.TRANSIENT_EXITS)
 def test_atomic_acceptance_preserves_bytes(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'accepted.bin';raw=b'accepted\x00bytes\r\n';m.frozen_wiki.atomic_write(p,raw);self.assertEqual(p.read_bytes(),raw)
 def test_parser_identity_unchanged(self):self.assertEqual(m.frozen_wiki.frozen.VERSION,'module4-external-parser-v1')
if __name__=='__main__':unittest.main()
