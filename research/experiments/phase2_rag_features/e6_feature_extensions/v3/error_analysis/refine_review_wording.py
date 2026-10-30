"""Correct a newly authored diagnostic statement after checking full saved precision."""
if "_H2_CTX" not in globals():
    raise RuntimeError("Use the verified saved-analysis context; direct execution is disabled")
_H2_CTX.source_gate(__file__)
from pathlib import Path
OUT=_H2_CTX.binding('OUT', 'scripts')
replacements=[
 ('Ίδια NLI/HHEM scores, διαφορετική OOF έκβαση',
  'Ίδια NLI2 και πρακτικά ίδια HHEM scores (διαφορά reference consistency περίπου 1,5×10⁻⁸), διαφορετική OOF έκβαση'),
 ('ίδια αποθηκευμένα NLI2/HHEM scores,',
  'ίδια αποθηκευμένα NLI2 scores και πρακτικά ίδια HHEM scores (διαφορά reference consistency περίπου 1,5×10⁻⁸),')]
files=['qualitative_notes.json','qualitative_review_by_id.json','diagnostic_table.json','E6_ERROR_ANALYSIS.md','build_report.py']
for name in files:
    p=OUT/name;text=_H2_CTX.io_path(p, 'r').read_text(encoding='utf-8');changed=text
    for a,b in replacements:changed=changed.replace(a,b)
    assert changed!=text,name
    _H2_CTX.io_path(p, 'w').write_text(changed,encoding='utf-8',newline='\n')
print('Updated only new analysis wording; no predictions/features changed')
