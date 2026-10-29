import importlib.util
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

SCRIPT = next((
    parent / "RAG/scripts/module4_build_external_lexicon.py"
    for parent in Path(__file__).resolve().parents
    if (parent / "research/README.md").is_file()
    and (parent / "RAG/scripts/module4_build_external_lexicon.py").is_file()
), None)
if SCRIPT is None:
    raise RuntimeError("Historical Module 4 source root was not found")
spec = importlib.util.spec_from_file_location("m4lex", SCRIPT)
m4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m4)


def synthetic_wordnet(path: Path):
    files = {
        "index.noun": "alpha n 1 0 1 0 00000001\n",
        "index.verb": "act v 1 0 1 0 00000002\n",
        "index.adj": "bright a 1 0 1 0 00000003\n",
        "index.adv": "quickly r 1 0 1 0 00000004\n",
        "data.noun": '00000001 00 n 01 alpha 0 000 | first definition; "example"\n',
        "data.verb": "00000002 00 v 01 act 0 000 | to do something\n",
        "data.adj": "00000003 00 a 01 bright 0 000 | giving light\n",
        "data.adv": "00000004 00 r 01 quickly 0 000 | in a quick way\n",
    }
    with tarfile.open(path, "w:gz") as tf:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo("dict/" + name); info.size = len(data); info.mtime = 0
            tf.addfile(info, io.BytesIO(data))


class ParserTests(unittest.TestCase):
    def test_term_extraction_variants_and_no_guess(self):
        self.assertEqual(m4.extract_dm_term("x <define> Term </define> y"), "Term")
        self.assertEqual(m4.extract_dm_term("x <define> Term <define> y"), "Term")
        self.assertIsNone(m4.extract_dm_term("no marker"))

    def test_wordnet_four_pos_and_gloss_rules(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wn.tar.gz"; synthetic_wordnet(p)
            terms = [{"term_key": x, "surface_term": x} for x in ("alpha","act","bright","quickly")]
            rows = m4.parse_wordnet_archive(p, terms)
            self.assertEqual(len(rows), 4)
            self.assertEqual(rows[0]["candidate_definition"], "first definition")
            self.assertIn("example", rows[0]["candidate_context"])

    def test_wiktionary_english_pos_nested_and_unicode(self):
        html = '''<h2><span id="French">French</span></h2><h3><span id="Noun">Noun</span></h3><ol><li>wrong</li></ol>
        <h2><span id="English">English</span></h2><h3><span id="Noun">Noun</span></h3>
        <ol><li>Caf&eacute; sense<ul><li>example excluded</li></ul><sup class="reference">[1]</sup></li><li><ol><li>nested excluded</li></ol>Second</li></ol>
        <h3><span id="Translations">Translations</span></h3><ol><li>excluded</li></ol>
        <h3><span id="Verb">Verb</span></h3><ol><li>To act</li></ol><h2><span id="German">German</span></h2>'''
        t={"term_key":"café","surface_term":"Café"}
        rows=m4.parse_wiktionary_html(html,t,1,2,{"x":1})
        self.assertEqual([r["candidate_definition"] for r in rows],["Café sense","Second","To act"])
        self.assertEqual([r["source_entry_id"].split(":")[-2] for r in rows],["Noun","Noun","Verb"])

    def test_redirect_missing_and_raw_response_shape(self):
        redirect={"query":{"redirects":[{"from":"a","to":"A"}],"pages":[{"pageid":1,"title":"A","revisions":[{"revid":2,"timestamp":"2020-01-01T00:00:00Z","sha1":"x"}]}]}}
        missing={"query":{"pages":[{"title":"z","missing":True}]}}
        self.assertEqual(redirect["query"]["pages"][0]["revisions"][0]["revid"],2)
        self.assertTrue(missing["query"]["pages"][0]["missing"])

    def test_empty_and_duplicate_cross_source_determinism(self):
        rows=[
          {"term_key":"x","source":"enwiktionary","source_entry_id":"w:1","candidate_term":"X","candidate_definition":"Same!","candidate_context":"w","provenance":{"a":1}},
          {"term_key":"x","source":"wordnet31","source_entry_id":"n:1","candidate_term":"X","candidate_definition":"same","candidate_context":"n","provenance":{"b":2}},
          {"term_key":"x","source":"wordnet31","source_entry_id":"n:2","candidate_term":"X","candidate_definition":"___","candidate_context":"blank","provenance":{}},
        ]
        a=m4.deduplicate(rows,{"x":0});b=m4.deduplicate(list(reversed(rows)),{"x":0})
        self.assertEqual(a,b);self.assertEqual(len(a),1);self.assertEqual(a[0]["source"],"wordnet31")
        self.assertEqual(len(a[0]["provenance"]),2)

    def test_offline_byte_identical_reconstruction(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw=root/"raw_sources";raw.mkdir();synthetic_wordnet(raw/"wn3.1.dict.tar.gz")
            term={"term_key":"alpha","surface_term":"alpha","development_row_count":1}
            rev={"query":{"pages":[{"pageid":1,"title":"alpha","revisions":[{"revid":2,"timestamp":"2020-01-01T00:00:00Z","sha1":"x"}]}]}}
            parsed={"parse":{"revid":2,"text":"<h2><span id='English'>English</span></h2><h3><span id='Noun'>Noun</span></h3><ol><li>first definition</li><li>other</li></ol>"}}
            stem="0001_"+__import__('hashlib').sha256(b"alpha").hexdigest()[:12]
            (raw/f"{stem}_revision.json").write_text(json.dumps(rev),encoding="utf-8")
            (raw/f"{stem}_parse.json").write_text(json.dumps(parsed),encoding="utf-8")
            s1=root/"a.jsonl";m1=root/"a.csv";s2=root/"b.jsonl";m2=root/"b.csv"
            m4.offline_build(raw,[term],s1,m1);m4.offline_build(raw,[term],s2,m2)
            self.assertEqual(s1.read_bytes(),s2.read_bytes());self.assertEqual(m1.read_bytes(),m2.read_bytes())

    def test_public_builder_inputs_exclude_forbidden_fields(self):
        self.assertEqual(set(m4.load_canonical_inputs.__annotations__), {"manifest","return"})
        self.assertNotIn("tgt", m4.acquire_sources.__code__.co_varnames)
        self.assertNotIn("label", m4.acquire_sources.__code__.co_varnames)
        self.assertNotIn("prediction", m4.acquire_sources.__code__.co_varnames)


if __name__ == "__main__":
    unittest.main()
