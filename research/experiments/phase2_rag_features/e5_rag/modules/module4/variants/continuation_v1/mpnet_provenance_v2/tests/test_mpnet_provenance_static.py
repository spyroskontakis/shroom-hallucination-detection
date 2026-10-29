import ast
import unittest
from pathlib import Path

SCRIPT = next((
    parent / "RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/scripts/module4_build_rag_features_pinned.py"
    for parent in Path(__file__).resolve().parents
    if (parent / "research/README.md").is_file()
    and (parent / "RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/scripts/module4_build_rag_features_pinned.py").is_file()
), None)
if SCRIPT is None:
    raise RuntimeError("Historical Module 4 source root was not found")
EXPECTED_REVISION="e8c3b32edf5434bc2275fc9bab85f82640a19130"

def parse_script():
    return ast.parse(SCRIPT.read_text(encoding="utf-8"),filename=str(SCRIPT))

class MpnetProvenanceStaticTests(unittest.TestCase):
    def test_mpnet_revision_constant_is_pinned(self):
        module=parse_script()
        revision=None
        for node in module.body:
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Name) and target.id=="MPNET_REVISION":
                        revision=ast.literal_eval(node.value)
        self.assertEqual(revision,EXPECTED_REVISION)

    def test_sentence_transformer_uses_pinned_revision_and_local_files_only(self):
        module=parse_script()
        calls=[node for node in ast.walk(module) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="SentenceTransformer"]
        self.assertEqual(len(calls),1)
        keywords={kw.arg:kw.value for kw in calls[0].keywords if kw.arg is not None}
        self.assertIn("revision",keywords)
        self.assertIsInstance(keywords["revision"],ast.Name)
        self.assertEqual(keywords["revision"].id,"MPNET_REVISION")
        self.assertIn("local_files_only",keywords)
        self.assertIs(keywords["local_files_only"].value,True)

if __name__=="__main__":unittest.main()
