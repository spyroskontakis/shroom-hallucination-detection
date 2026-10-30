import ast,importlib.util,os,socket,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FEATURE=Path((__import__('os').environ.get('SHROOM_PROJECT_ROOT', '.') + '/RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/scripts/module4_build_rag_features_pinned.py'))
OVERLAP=Path((__import__('os').environ.get('SHROOM_PROJECT_ROOT', '.') + '/RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/scripts/module4_exact_overlap_audit_pinned.py'))
class ReplayStaticTests(unittest.TestCase):
 def test_pins_and_local_only_in_both_loaders(self):
  a=FEATURE.read_text();b=OVERLAP.read_text();self.assertIn("revision=MPNET_REVISION",a);self.assertIn("revision=frozen.MPNET_REVISION",b);self.assertIn("local_files_only=True",a);self.assertIn("local_files_only=True",b)
 def test_frozen_semantics_markers(self):
  a=FEATURE.read_text();self.assertIn('TOP_K=5',a);self.assertIn("f\"{row['term']}\\n{row['src']}\"",a);self.assertIn('nli([(definition,row["tgt"])',a);self.assertIn('encoding="utf-8-sig"',a);self.assertIn('lineterminator="\\n"',a)
 def test_overlap_historical_logic(self):
  b=OVERLAP.read_text();self.assertIn('unicodedata.normalize("NFKC"',b);self.assertIn("row['task']=='DM'",b);self.assertIn("candidate_definition'])==norm(row['tgt'])",b)
 def test_safe_output_boundary(self):
  root=ROOT.resolve();inside=(root/'features'/'x.csv').resolve();inside.relative_to(root)
  with self.assertRaises(ValueError):(Path(root.drive+'\\outside.csv').resolve()).relative_to(root)
 def test_process_network_guard_is_active(self):
  self.assertEqual(socket.socket.connect.__module__,'sitecustomize');self.assertEqual(socket.getaddrinfo.__module__,'sitecustomize')
 def test_python_syntax(self):ast.parse(FEATURE.read_text());ast.parse(OVERLAP.read_text());ast.parse((ROOT/'scripts'/'run_replay.py').read_text())
if __name__=='__main__':unittest.main()
