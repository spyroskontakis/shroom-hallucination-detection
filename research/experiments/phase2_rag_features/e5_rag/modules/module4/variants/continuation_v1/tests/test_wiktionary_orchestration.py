import csv, importlib.util, json, sys, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "module4_build_wiktionary_lexicon.py"
spec = importlib.util.spec_from_file_location("wikt_v1", SCRIPT); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class OrchestrationTests(unittest.TestCase):
    def test_version_and_no_wordnet_endpoint(self):
        self.assertEqual(module.VERSION, "module4-wiktionary-only-orchestration-v1")
        self.assertNotIn("WORDNET_URL", module.__dict__)

    def test_missing_page_is_no_sense_found_and_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw=root/"raw_sources";raw.mkdir()
            term={"term_key":"alpha","surface_term":"alpha","development_row_count":1}
            stem=module.stem_for(1,"alpha")
            (raw/f"{stem}_revision.json").write_text(json.dumps({"query":{"pages":[{"title":"alpha","missing":True}]}}),encoding="utf-8")
            a=root/"a.jsonl";am=root/"a.csv";b=root/"b.jsonl";bm=root/"b.csv"
            r1=module.offline_build(raw,[term],a,am);r2=module.offline_build(raw,[term],b,bm)
            self.assertEqual(a.read_bytes(),b.read_bytes());self.assertEqual(am.read_bytes(),bm.read_bytes())
            self.assertEqual(r1["status_counts"],{"NO_SENSE_FOUND":1});self.assertEqual(r1,r2)

    def test_missing_parse_is_request_failed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw=root/"raw_sources";raw.mkdir();term={"term_key":"alpha","surface_term":"alpha","development_row_count":1};stem=module.stem_for(1,"alpha")
            payload={"query":{"pages":[{"pageid":1,"title":"alpha","revisions":[{"revid":2,"timestamp":"2020-01-01T00:00:00Z","sha1":"x"}]}]}}
            (raw/f"{stem}_revision.json").write_text(json.dumps(payload),encoding="utf-8")
            result=module.offline_build(raw,[term],root/"s.jsonl",root/"m.csv")
            self.assertEqual(result["status_counts"],{"SOURCE_REQUEST_FAILED":1})

    def test_frozen_parser_semantics_are_reused(self):
        self.assertIs(module.frozen.parse_wiktionary_html, sys.modules["module4_build_external_lexicon"].parse_wiktionary_html)
        self.assertIs(module.frozen.deduplicate, sys.modules["module4_build_external_lexicon"].deduplicate)


if __name__ == "__main__": unittest.main()
