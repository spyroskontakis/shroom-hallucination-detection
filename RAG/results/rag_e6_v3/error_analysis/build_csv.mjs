// Author the requested flat diagnostic table with Artifact Tool; export RFC4180 CSV.
// CSV has no styling or workbook formulas. Source strings and all numeric values are verified.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook} from '@oai/artifact-tool';
const out=path.dirname(fileURLToPath(import.meta.url));
const flag=process.argv.includes('--refresh-analysis-output')?'w':'wx';
const data=JSON.parse(await fs.readFile(path.join(out,'diagnostic_table.json'),'utf8'));
const {columns,rows}=data;
if(rows.length!==561 || new Set(rows.map(r=>r.canonical_id)).size!==561)throw Error('ID count');
const textColumns=new Set(['canonical_id','task','src','tgt','hyp','selected_external_definition',
 'selected_evidence_id','reference_field','human_votes_json','correctness_group','missing_fields',
 'qualitative_tags','qualitative_note']);
const values=[columns,...rows.map(r=>columns.map(k=>r[k]===null?null:textColumns.has(k)?r[k]:Number(r[k])))];
const wb=Workbook.create();const sheet=wb.worksheets.add('Diagnostics');
sheet.getRangeByIndexes(0,0,values.length,columns.length).values=values;
wb.recalculate();
const actual=sheet.getRangeByIndexes(0,0,values.length,columns.length).values;
for(let i=0;i<values.length;i++)for(let j=0;j<columns.length;j++){
 const a=actual[i][j],b=values[i][j];
 if(a!==b && !(a===null&&b==='') && !(a===''&&b===null))throw Error(`Round trip mismatch row=${i} column=${columns[j]}`);
}
// Use authoritative recovered cell values; CSV carries exact JS numeric values, not display formatting.
const quote=v=>v===null||v===undefined?'':`"${String(v).replaceAll('"','""')}"`;
const csv=actual.map(row=>row.map(quote).join(',')).join('\r\n')+'\r\n';
await fs.writeFile(path.join(out,'E6_DIAGNOSTIC_TABLE.csv'),csv,{encoding:'utf8',flag});
await fs.writeFile(path.join(out,'csv_authoring_check.json'),JSON.stringify({status:'PASS',rows:561,columns:columns.length,
 engine:'@oai/artifact-tool',format:'CSV UTF-8 RFC4180',all_cells_round_trip:true,rendering:'not applicable to plain CSV',
 null_policy:'empty CSV fields; missing_fields and evidence_available distinguish missing versus score fallback'},null,2),{flag});
console.log(JSON.stringify({status:'PASS',rows:561,columns:columns.length}));
