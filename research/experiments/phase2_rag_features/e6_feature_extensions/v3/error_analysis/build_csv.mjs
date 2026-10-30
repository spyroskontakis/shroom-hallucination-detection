// CURRENT_ADAPTED: explicit input/package identity and external exclusive outputs.
// Historical source is retained at the immutable original public Git revision.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
export const MODE='CURRENT_ADAPTED';
export const HISTORICAL_SOURCE_SHA256='e2063e11e3fcf8fe798fe1609a647bf83c45e25488c1436f62f3bedd38b22080';
export const ORIGINAL_INPUT_SHA256='7004fe8a1bc070d8a6508bba9f1eaa5241a7d6fbee150c9f1fb30773448bf472';
const digest=b=>createHash('sha256').update(b).digest('hex');
async function checked(value) {
 if(typeof value!=='string'||!path.isAbsolute(value))throw Error('ABSOLUTE_PATH_REQUIRED');
 const p=path.normalize(value);
 for(let q=p;;q=path.dirname(q)) {
  try {if((await fs.lstat(q)).isSymbolicLink())throw Error('LINK_PATH_REJECTED');}
  catch(e){if(e.code!=='ENOENT')throw e;}
  if(path.dirname(q)===q)break;
 }
 return p;
}
async function exists(p){try{await fs.lstat(p);return true;}catch(e){if(e.code==='ENOENT')return false;throw e;}}
function within(p,root){const d=path.relative(root,p);return d===''||(!d.startsWith('..'+path.sep)&&d!=='..'&&!path.isAbsolute(d));}
async function outsideGit(p) {
 for(let q=p;;q=path.dirname(q)) {
  if(await exists(path.join(q,'.git')))throw Error('GIT_WRITE_ROOT_REJECTED');
  if(path.dirname(q)===q)break;
 }
}
function shape(data){
 if(!Array.isArray(data.columns)||!Array.isArray(data.rows))throw Error('INVALID_TABLE_SCHEMA');
 if(data.rows.length!==561||new Set(data.rows.map(r=>r.canonical_id)).size!==561)throw Error('ID count');
}
export async function plan(options) {
 const input=await checked(options.input),run=await checked(options.run);
 const entry=await checked(options.packageEntry);
 if(!/^[a-f0-9]{64}$/.test(options.packageSha256||''))throw Error('PACKAGE_PIN_REQUIRED');
 if(await exists(run))throw Error('EXISTING_OUTPUT_REJECTED');
 if(!(await fs.stat(path.dirname(run))).isDirectory())throw Error('OUTPUT_PARENT_REQUIRED');
 await outsideGit(run);
 if(within(input,run)||within(entry,run))throw Error('READ_WRITE_ROOT_OVERLAP');
 const raw=await fs.readFile(input);
 if(digest(raw)!==ORIGINAL_INPUT_SHA256)throw Error('ORIGINAL_INPUT_MISSING_OR_WRONG');
 const data=JSON.parse(raw.toString('utf8'));shape(data);
 if(digest(await fs.readFile(entry))!==options.packageSha256)throw Error('PACKAGE_SOURCE_IDENTITY_MISMATCH');
 return Object.freeze({input,run,entry,data,packageSha256:options.packageSha256});
}
export function render(data,Workbook) {
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
 return {csv,columns:columns.length};
}
export async function persist(run,result,record) {
 run=await checked(run);await outsideGit(run);
 if(await exists(run))throw Error('EXISTING_OUTPUT_REJECTED');
 // This generic writer certifies no input/scientific provenance by itself.
 await fs.mkdir(run,{recursive:false});
 await fs.writeFile(path.join(run,'E6_DIAGNOSTIC_TABLE.csv'),result.csv,{encoding:'utf8',flag:'wx'});
 await fs.writeFile(path.join(run,'csv_authoring_check.json'),JSON.stringify(record,null,2),{encoding:'utf8',flag:'wx'});
}
export async function author(options) {
 const ctx=await plan(options); // All identity/path checks precede import or writes.
 if(!process.permission)throw Error('NODE_PERMISSION_MODE_REQUIRED');
 if(process.execArgv.some(x=>/^--allow-(addons|worker|child-process|wasi)(=|$)/.test(x))||/--allow-(addons|worker|child-process|wasi)/.test(process.env.NODE_OPTIONS||''))throw Error('NATIVE_CHILD_WORKER_CAPABILITY_REJECTED');
 if(process.permission.has('fs.write',fileURLToPath(import.meta.url))||
    process.permission.has('fs.write',ctx.input))throw Error('READONLY_SOURCE_INPUT_REQUIRED');
 const {Workbook}=await import(pathToFileURL(ctx.entry).href);
 if(typeof Workbook?.create!=='function')throw Error('WORKBOOK_API_UNAVAILABLE');
 const result=render(ctx.data,Workbook);
 const record={status:'PASS',mode:MODE,rows:561,columns:result.columns,
  engine:'@oai/artifact-tool',format:'CSV UTF-8 RFC4180',all_cells_round_trip:true,
  rendering:'not applicable to plain CSV',input_sha256:ORIGINAL_INPUT_SHA256,
  package_entry_sha256:ctx.packageSha256,historical_runtime:'NOT VERIFIED',
  null_policy:'empty CSV fields; missing_fields and evidence_available distinguish missing versus score fallback'};
 await persist(ctx.run,result,record);
 return record;
}
export async function main(argv=process.argv.slice(2)) {
 if(argv.includes('--refresh-analysis-output'))throw Error('HISTORICAL_OVERWRITE_OPTION_REJECTED');
 const options={};const keys={'--input':'input','--run':'run','--package-entry':'packageEntry','--package-sha256':'packageSha256'};
 let inspect=false;
 for(let i=0;i<argv.length;i++){
  if(argv[i]==='--plan'){inspect=true;continue;}
  if(!(argv[i] in keys)||!argv[i+1]||argv[i+1].startsWith('--')||keys[argv[i]] in options)throw Error('INVALID_CLI_OPTION');
  options[keys[argv[i]]]=argv[++i];
 }
 if(Object.keys(options).length!==4)throw Error('EXPLICIT_INPUT_RUN_PACKAGE_AND_PIN_REQUIRED');
 const result=inspect?await plan(options):await author(options);
 console.log(JSON.stringify(inspect?{mode:MODE,source_checks:'PASS',runtime:'NOT VERIFIED',writes:0}:result));
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 main().catch(e=>{console.error('Authoring rejected: '+e.message);process.exitCode=2;});
}
