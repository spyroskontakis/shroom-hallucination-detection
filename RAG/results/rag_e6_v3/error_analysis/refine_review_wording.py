"""Correct a newly authored diagnostic statement after checking full saved precision."""
from pathlib import Path
OUT=Path(__file__).resolve().parent
replacements=[
 ('Ίδια NLI/HHEM scores, διαφορετική OOF έκβαση',
  'Ίδια NLI2 και πρακτικά ίδια HHEM scores (διαφορά reference consistency περίπου 1,5×10⁻⁸), διαφορετική OOF έκβαση'),
 ('ίδια αποθηκευμένα NLI2/HHEM scores,',
  'ίδια αποθηκευμένα NLI2 scores και πρακτικά ίδια HHEM scores (διαφορά reference consistency περίπου 1,5×10⁻⁸),')]
files=['qualitative_notes.json','qualitative_review_by_id.json','diagnostic_table.json','E6_ERROR_ANALYSIS.md','build_report.py']
for name in files:
    p=OUT/name;text=p.read_text(encoding='utf-8');changed=text
    for a,b in replacements:changed=changed.replace(a,b)
    assert changed!=text,name
    p.write_text(changed,encoding='utf-8',newline='\n')
print('Updated only new analysis wording; no predictions/features changed')
