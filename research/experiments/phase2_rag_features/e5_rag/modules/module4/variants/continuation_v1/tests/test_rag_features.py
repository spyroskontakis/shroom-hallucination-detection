import importlib.util, math, tempfile, unittest
from pathlib import Path
import numpy as np
SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"module4_build_rag_features.py";spec=importlib.util.spec_from_file_location("features_v1",SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def embed(texts):
    return np.asarray([[float(len(t)%7+1),float(sum(map(ord,t))%11+1),1.0] for t in texts])
def nli(pairs):return [{"contradiction":0.2,"neutral":0.3,"entailment":0.5} for _ in pairs]
def evidence(i=1):return {"evidence_id":f"e{i}","term_key":"alpha","source":"enwiktionary","source_entry_id":f"wiktionary:1:2:Noun:{i}","candidate_term":"alpha","candidate_definition":f"alpha meaning {i}","candidate_context":f"Noun: alpha meaning {i}","provenance":[]}
def rows():
    base=[]
    for i in range(561):
        task="DM" if i<211 else "MT" if i<427 else "PG";base.append({"example_id":f"id{i:03d}","task":task,"term":"alpha" if task=="DM" else "","src":"source","tgt":"alpha meaning","rag_applicable":"1" if task=="DM" else "0"})
    return base

class FeatureTests(unittest.TestCase):
    def test_schema_and_topk(self):self.assertEqual(len(m.FEATURES),7);self.assertEqual(m.TOP_K,5)
    def test_nli_direction_and_mapping(self):
        seen=[]
        def capture(pairs):seen.extend(pairs);return nli(pairs)
        m.row_features(rows()[0],[evidence()],embed,capture);self.assertEqual(seen,[('alpha meaning 1','alpha meaning')]);self.assertEqual(m.NLI_LABELS,{0:'CONTRADICTION',1:'NEUTRAL',2:'ENTAILMENT'})
    def test_deterministic_ranking_and_aggregation(self):
        a=m.row_features(rows()[0],[evidence(i) for i in range(8)],embed,nli);b=m.row_features(rows()[0],list(reversed([evidence(i) for i in range(8)])),embed,nli);self.assertEqual(a,b);self.assertEqual(a['rag_sense_count'],5);self.assertEqual(a['rag_evidence_available'],1)
    def test_no_evidence_and_non_dm_zero(self):
        for row in (rows()[0],rows()[211],rows()[427]):
            out=m.row_features(row,[],embed,nli);self.assertTrue(all(float(out[f])==0 for f in m.FEATURES))
    def test_jaccard_and_ranges(self):self.assertEqual(m.lexical_jaccard('A b','b c'),1/3)
    def test_rejections(self):
        with self.assertRaises(ValueError):m.validate_input_schema(['example_id','label'])
        bad=evidence();bad['source']='wordnet31'
        with self.assertRaises(ValueError):m.validate_snapshot([bad])
    def test_duplicate_ids_and_evidence(self):
        rr=rows();rr[-1]['example_id']=rr[0]['example_id']
        with self.assertRaises(ValueError):m.build(rr,[evidence()],embed,nli)
        with self.assertRaises(ValueError):m.validate_snapshot([evidence(),evidence()])
    def test_561_rows_mtpg_zeros_finite_and_stable(self):
        out1=m.build(rows(),[evidence()],embed,nli);out2=m.build(rows(),[evidence()],embed,nli);self.assertEqual(out1,out2);self.assertEqual(len(out1),561)
        for r in out1[211:]:self.assertTrue(all(r[f]==0 for f in m.FEATURES))
        self.assertTrue(all(math.isfinite(float(r[f])) for r in out1 for f in m.FEATURES))
    def test_byte_identical_serialization(self):
        out=m.build(rows(),[evidence()],embed,nli)
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'a.csv';b=Path(td)/'b.csv';m.write_csv(a,out);m.write_csv(b,out);self.assertEqual(a.read_bytes(),b.read_bytes())

if __name__=='__main__':unittest.main()
