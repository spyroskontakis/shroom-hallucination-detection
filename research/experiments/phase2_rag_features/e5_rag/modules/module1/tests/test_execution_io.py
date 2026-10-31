"""Standalone offline IO tests consolidated from the verified migration audit.

Run through the repository verifier with explicit external scratch and source pins.
Only IO/cache definitions are tested; no scientific notebook/API cells run.
"""

def main():
    import os,sys,json,ast,hashlib,unittest,time,traceback,contextlib,uuid,io
    from pathlib import Path
    scratch=Path(os.environ["M1_TEST_SCRATCH"]).resolve()
    sources=json.loads(os.environ["M1_NOTEBOOK_PINS"])
    allowed={Path(x).resolve() for x in sources}
    stdlib=Path(sys.base_prefix).resolve()
    assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
    events={"writes":0,"network":0,"subprocess":0,"ml_imports":0,"outside_writes":0}
    def under(p,root):return p==root or p.is_relative_to(root)
    def guard(event,args):
     if event.startswith("socket."):events["network"]+=1;raise PermissionError("network disabled")
     if event in ("subprocess.Popen","os.system","os.exec","os.posix_spawn"):events["subprocess"]+=1;raise PermissionError("subprocess disabled")
     if event=="import" and args[0].split(".")[0] in ("numpy","pandas","google","torch","transformers","requests"):
      events["ml_imports"]+=1;raise PermissionError("ML/API import disabled")
     if event=="open":
      if isinstance(args[0],int):return
      p=Path(os.fsdecode(args[0])).resolve()
      mode,flags=args[1:3]
      write=(isinstance(mode,str) and any(x in mode for x in "wax+"))or(isinstance(flags,int)and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC)))
      if write:
       if not under(p,scratch):events["outside_writes"]+=1;raise PermissionError("write outside scratch")
       events["writes"]+=1
      elif not(under(p,scratch)or under(p,stdlib)or p in allowed):raise PermissionError("undeclared read")
     if event in ("os.mkdir","os.remove","os.rmdir","os.rename","os.chmod","os.utime","os.truncate","os.link","os.symlink"):
      for value in (args[:2] if event in ("os.rename","os.link","os.symlink") else args[:1]):
       if isinstance(value,int):continue
       p=Path(os.fsdecode(value)).resolve()
       if not under(p,scratch):events["outside_writes"]+=1;raise PermissionError("mutation outside scratch")
    sys.addaudithook(guard)
    loaded=[]
    for filename,pin in sources.items():
     raw=Path(filename).read_bytes();assert hashlib.sha256(raw).hexdigest()==pin
     j=json.loads(raw);setup=ast.parse("".join(j["cells"][4]["source"]))
     selected=[n for n in setup.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and(n.name.startswith("_module1_")or n.name=="_Module1IO")]
     cachecell=28 if "gemini_trial" in filename else 27
     selected.extend(n for n in ast.parse("".join(j["cells"][cachecell]["source"])).body if isinstance(n,ast.FunctionDef)and n.name in("load_cache","append_cache"))
     ns={"Path":Path,"os":os,"json":json,"hashlib":hashlib,"_module1_contextlib":contextlib,"_module1_uuid":uuid}
     before=events["writes"];exec(compile(ast.Module(body=selected,type_ignores=[]),filename,"exec"),ns)
     assert events["writes"]==before
     loaded.append((filename,ns))
    class T(unittest.TestCase):
     def setUp(self):
      self.case=scratch/uuid.uuid4().hex;self.case.mkdir();self.data=self.case/"inputs";self.data.mkdir()
      self.temp=self.case/"temporary";self.temp.mkdir();self.run=self.case/"run";self.env_before=dict(os.environ)
      self.C=self.namespace["_Module1IO"];self.ctx=self.C(self.data,self.run);self.namespace["_M1_IO"]=self.ctx
     def tearDown(self):
      os.environ.clear();os.environ.update(self.env_before)
     def failcall(self,call):
      with self.assertRaises((ValueError,FileExistsError,KeyError,FileNotFoundError)):call()
     def record(self,index=1):
      return {"development_index":index,"mode":"baseline","model":"synthetic-model","prompt_hash":"synthetic-"+str(index)}
     def test_construction_has_no_writes(self):
      self.assertFalse(self.run.exists())
     def test_reparse_root_rejected(self):
      fixture=Path(os.environ["M1_REPARSE"])
      self.assertTrue(fixture.lstat().st_file_attributes&0x400)
      self.failcall(lambda:self.C(self.data,fixture/"new-run"))
     def test_unc_root_rejected(self):
      self.failcall(lambda:self.C(self.data,Path("\\\\server\\share\\new-run")))
     def test_relative_run_rejected(self):
      self.failcall(lambda:self.C(self.data,"relative"))
     def test_traversal_rejected(self):
      self.failcall(lambda:self.C(self.data,self.case/"a"/".."/"run"))
     def test_missing_inputs_rejected(self):
      self.failcall(lambda:self.C(self.case/"missing",self.run))
     def test_existing_run_rejected(self):
      self.run.mkdir();self.failcall(lambda:self.C(self.data,self.run))
     def test_missing_run_parent_rejected(self):
      self.failcall(lambda:self.C(self.data,self.case/"missing"/"run"))
     def test_input_run_overlap_rejected(self):
      self.failcall(lambda:self.C(self.data,self.data/"run"))
     def test_git_run_rejected(self):
      fake=self.case/"git";fake.mkdir();(fake/".git").write_text("synthetic")
      self.failcall(lambda:self.C(self.data,fake/"run"))
     def test_run_appearance_rejected(self):
      self.run.mkdir();self.failcall(lambda:self.ctx.append_cache(self.ctx.cache_path,self.record()))
     def test_outside_cache_rejected(self):
      self.failcall(lambda:self.ctx.append_cache(self.case/"outside.jsonl",self.record()))
     def test_device_name_rejected(self):
      self.failcall(lambda:self.C(self.data,self.case/"NUL"))
     def test_trailing_dot_rejected(self):
      self.failcall(lambda:self.C(self.data,self.case/"run."))
     def test_alternate_stream_rejected(self):
      self.failcall(lambda:self.C(self.data,self.case/"run:stream"))
     def test_missing_historical_cache_rejected(self):
      self.failcall(lambda:self.C(self.data,self.run,self.case/"missing.jsonl"))
     def test_historical_run_overlap_rejected(self):
      history=self.case/"history";history.mkdir();cache=history/"cache.jsonl";cache.write_text("{}\n")
      self.failcall(lambda:self.C(self.data,history/"run",cache))
     def test_empty_cache_no_writes(self):
      self.assertEqual(self.namespace["load_cache"](self.ctx.cache_path),{})
      self.assertFalse(self.run.exists())
     def test_owned_append_preserves_first_record(self):
      self.namespace["append_cache"](self.ctx.cache_path,self.record(1));first=self.ctx.cache_path.read_bytes()
      self.namespace["append_cache"](self.ctx.cache_path,self.record(2))
      self.assertTrue(self.ctx.cache_path.read_bytes().startswith(first))
      self.assertEqual(len(self.namespace["load_cache"](self.ctx.cache_path)),2)
     def test_unowned_cache_not_overwritten(self):
      self.ctx._ensure_run();self.ctx.cache_path.write_text("SYNTHETIC_UNOWNED\n");b=self.ctx.cache_path.read_bytes()
      self.failcall(lambda:self.ctx.append_cache(self.ctx.cache_path,self.record()))
      self.assertEqual(self.ctx.cache_path.read_bytes(),b)
     def test_modified_owned_cache_rejected(self):
      self.ctx.append_cache(self.ctx.cache_path,self.record());self.ctx.cache_path.write_text("TAMPER\n")
      self.failcall(lambda:self.ctx.append_cache(self.ctx.cache_path,self.record(2)))
     def test_historical_cache_read_only_seed(self):
      history=self.case/"history";history.mkdir();cache=history/"cache.jsonl"
      cache.write_text(json.dumps(self.record(1))+"\n");b=cache.read_bytes()
      ctx=self.C(self.data,self.run,cache);self.namespace["_M1_IO"]=ctx
      self.assertEqual(len(self.namespace["load_cache"](ctx.cache_path)),1)
      self.namespace["append_cache"](ctx.cache_path,self.record(2))
      self.assertEqual(len(self.namespace["load_cache"](ctx.cache_path)),2)
      self.assertEqual(cache.read_bytes(),b)
     def test_historical_mutation_rejected(self):
      history=self.case/"history";history.mkdir();cache=history/"cache.jsonl";cache.write_text(json.dumps(self.record())+"\n")
      ctx=self.C(self.data,self.run,cache);cache.write_text("TAMPER\n")
      self.failcall(lambda:ctx.cache_sources(ctx.cache_path))
     def test_temporary_root_overlap_rejected(self):
      self.failcall(lambda:self.ctx.configure_temporary_root(self.data))
     def test_missing_temporary_root_rejected(self):
      self.failcall(lambda:self.ctx.configure_temporary_root(self.case/"missing"))
     def test_temporary_environment_no_writes(self):
      before=events["writes"];self.ctx.configure_temporary_root(self.temp)
      self.assertEqual(events["writes"],before);self.assertEqual(os.environ["TEMP"],str(self.temp))
      self.assertEqual(os.environ["HF_HUB_OFFLINE"],"1")
     def test_input_escape_rejected(self):
      self.failcall(lambda:self.ctx.input_path(self.case/"outside.json"))
     def test_synthetic_selftest_uses_run_only(self):
      with self.ctx.selftest_cache() as path:
       self.assertEqual(path.parent,self.run);self.ctx.append_cache(path,self.record())
       self.assertEqual(len(self.namespace["load_cache"](path)),1)
      self.assertTrue(path.exists())
    class Result(unittest.TestResult):
     def __init__(self):super().__init__();self.rows=[];self.current=None
     def startTest(self,test):
      super().startTest(test);self.current={"case":test.id(),"status":"PASS"}
     def stopTest(self,test):self.rows.append(self.current);super().stopTest(test)
     def addFailure(self,test,err):
      self.current.update(status="FAIL",detail="".join(traceback.format_exception(*err)));super().addFailure(test,err)
     def addError(self,test,err):
      self.current.update(status="FAIL",detail="".join(traceback.format_exception(*err)));super().addError(test,err)
    suite=unittest.TestSuite()
    for i,(filename,ns) in enumerate(loaded):
     cls=type("Module1Trial"if"gemini_trial"in filename else"Module1Main",(T,),{"namespace":ns})
     suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    res=Result();start=time.monotonic()
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):suite.run(res)
    out={"python":sys.version,"tests":res.testsRun,"passed":sum(x["status"]=="PASS"for x in res.rows),"failed":sum(x["status"]!="PASS"for x in res.rows),"rows":res.rows,"audit_events":events,"seconds":round(time.monotonic()-start,3),"scope":"Actual AST-extracted IO class plus load_cache/append_cache only; no notebook setup/scientific/API cell execution","notebook_pins":sources}
    print(json.dumps(out));raise SystemExit(0 if out["failed"]==0 else 2)


if __name__ == "__main__":
    main()
