from pathlib import Path
exec(compile(Path(__file__).with_name('recover.py').read_text(encoding='utf-8').split('for directory,dirs,files in os.walk(ROOT):')[0],str(Path(__file__).with_name('recover.py')),'exec'))
base=json.loads((HERE/'SEARCH_INVENTORY.json').read_text(encoding='utf-8'))
# Review all local text objects with broader mapping markers, including generic definition mappings.
for item in base['file_inventory']:
    p=ROOT/item['path']
    if p.suffix.lower() in EXT and item['size']<=100_000_000 and not any(x in p.name.lower() for x in ['credential','service-account','service_account','.env','token.json']):
        scan(p.read_bytes(),item['path'],str(item['mtime_ns']))
raw=git('fsck','--full','--unreachable','--no-reflogs').decode()
(HERE/'GIT_UNREACHABLE_INVENTORY.txt').write_text(raw,encoding='utf-8')
oids=[line.split()[2] for line in raw.splitlines() if line.startswith('unreachable blob ')]
proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for oid in oids:
    proc.stdin.write((oid+'\n').encode());proc.stdin.flush()
    header=proc.stdout.readline().decode().split();size=int(header[2]);data=proc.stdout.read(size);proc.stdout.read(1)
    if size<=100_000_000:
        scan(data,'git-unreachable:'+oid)
        if zipfile.is_zipfile(io.BytesIO(data)):archive(data,'git-unreachable:'+oid)
proc.stdin.close();proc.wait()
save('SUPPLEMENTARY_SEARCH.json',{'unreachable_blobs_examined':len(oids),'counts':dict(counts),'errors':errors,'candidates':candidates,'definition_objects':records})
print(json.dumps({'unreachable_blobs':len(oids),'candidates':candidates,'errors':errors},ensure_ascii=False))
