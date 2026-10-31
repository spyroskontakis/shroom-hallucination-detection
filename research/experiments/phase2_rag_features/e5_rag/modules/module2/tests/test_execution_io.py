"""Standalone offline IO tests consolidated from the verified migration audit.

Run through the repository verifier with explicit external scratch and source pins.
Only IO/cache definitions are tested; no scientific notebook/API cells run.
"""

def main():
    import sys,os,json,time,hashlib,importlib.util,unittest,io,uuid
    from pathlib import Path
    from contextlib import redirect_stdout,redirect_stderr
    scratch=Path(os.environ["MODULE2_TEST_ROOT"]);helper=Path(os.environ["MODULE2_HELPER"])
    stdlib=Path(sys.base_prefix)
    events={"writes":0,"blocked_write":0,"network":0,"subprocess":0,"ml_imports":0}
    def inside(p,root):return p==root or p.is_relative_to(root)
    def guard(event,args):
     if event.startswith("socket."):events["network"]+=1;raise PermissionError("Network forbidden")
     if event in ("subprocess.Popen","os.system","os.exec","os.posix_spawn"):events["subprocess"]+=1;raise PermissionError("Subprocess forbidden")
     if event=="import" and str(args[0]).split(".")[0] in {"numpy","pandas","torch","transformers","sentence_transformers","rank_bm25"}:
      events["ml_imports"]+=1;raise PermissionError("ML import forbidden in synthetic tests")
     if event=="open" and not isinstance(args[0],int):
      p=Path(os.fsdecode(args[0])).resolve()
      mode,flags=args[1:3]
      write=(isinstance(mode,str) and any(c in mode for c in "wax+")) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
      if write:
       if not inside(p,scratch):events["blocked_write"]+=1;raise PermissionError("Write outside synthetic root")
       events["writes"]+=1
      elif not (inside(p,scratch.parent) or inside(p,stdlib) or p == helper.resolve()):raise PermissionError("Undeclared read")
     if event in ("os.mkdir","os.remove","os.rmdir","os.rename","os.link","os.symlink","os.truncate"):
      for v in args[:2] if event in ("os.rename","os.link","os.symlink") else args[:1]:
       if isinstance(v,int):continue
       p=Path(os.fsdecode(v)).resolve()
       if not inside(p,scratch):events["blocked_write"]+=1;raise PermissionError("Mutation outside synthetic root")
    sys.addaudithook(guard)
    assert sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site
    before_env=dict(os.environ);before_entries=list(scratch.rglob("*"))
    raw=helper.read_bytes();assert hashlib.sha256(raw).hexdigest()==os.environ["MODULE2_HELPER_PIN"]
    spec=importlib.util.spec_from_file_location("_module2_synthetic",helper)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    assert before_env==dict(os.environ) and before_entries==list(scratch.rglob("*")) and events["writes"]==0
    assert not {"numpy","pandas","torch","transformers","sentence_transformers"}&set(sys.modules)
    class T(unittest.TestCase):
     def setUp(self):
      self.base=scratch/uuid.uuid4().hex;self.base.mkdir()
      self.inp=self.base/"input";self.inp.mkdir()
      self.ev=self.base/"evidence";self.ev.mkdir()
      self.run=self.base/"new_run";self.cache=self.base/"cache"
     def ctx(self,**k):
      d=dict(input_root=self.inp,evidence_root=self.ev,run_dir=self.run);d.update(k);return m.Module2Context(**d)
     def test_plan_no_writes(self):
      before=list(self.base.iterdir());c=self.ctx();self.assertEqual(before,list(self.base.iterdir()))
     def test_relative_root_rejected(self):
      with self.assertRaises(ValueError):self.ctx(run_dir=Path("relative"))
     def test_traversal_root_rejected(self):
      with self.assertRaises(ValueError):self.ctx(run_dir=self.base/"a"/".."/"b")
     def test_existing_run_rejected(self):
      self.run.mkdir()
      with self.assertRaises(ValueError):self.ctx()
     def test_existing_file_run_rejected(self):
      self.run.write_bytes(b"keep")
      with self.assertRaises(ValueError):self.ctx()
      self.assertEqual(self.run.read_bytes(),b"keep")
     def test_missing_run_parent_rejected(self):
      with self.assertRaises(ValueError):self.ctx(run_dir=self.base/"missing"/"run")
     def test_missing_inputs_rejected(self):
      with self.assertRaises(ValueError):self.ctx(input_root=self.base/"missing")
     def test_input_overlap_rejected(self):
      with self.assertRaises(ValueError):self.ctx(run_dir=self.inp/"out")
     def test_evidence_overlap_rejected(self):
      with self.assertRaises(ValueError):self.ctx(run_dir=self.ev/"out")
     def test_git_ancestor_rejected(self):
      (self.base/".git").write_text("synthetic worktree")
      with self.assertRaises(ValueError):self.ctx()
     def test_cache_run_overlap_rejected(self):
      with self.assertRaises(ValueError):self.ctx(cache_dir=self.run,write_cache=True)
     def test_missing_read_cache_rejected(self):
      with self.assertRaises(ValueError):self.ctx(cache_dir=self.cache)
     def test_unknown_existing_cache_rejected(self):
      self.cache.mkdir()
      with self.assertRaises(ValueError):self.ctx(cache_dir=self.cache,write_cache=True)
     def test_read_cache_cannot_be_written(self):
      self.cache.mkdir();c=self.ctx(cache_dir=self.cache)
      with self.assertRaises(ValueError):c.write_text(self.cache/"file","blocked")
     def test_exclusive_run_text(self):
      c=self.ctx();p=self.run/"results"/"a.txt";c.write_text(p,"synthetic")
      self.assertEqual(p.read_text(),"synthetic")
     def test_existing_output_never_overwritten(self):
      c=self.ctx();p=self.run/"a";c.write_text(p,"keep")
      with self.assertRaises(FileExistsError):c.write_text(p,"wrong")
      self.assertEqual(p.read_text(),"keep")
     def test_outside_write_rejected(self):
      c=self.ctx()
      with self.assertRaises(ValueError):c.write_text(self.base/"outside","wrong")
     def test_output_traversal_rejected(self):
      c=self.ctx()
      with self.assertRaises(ValueError):c.write_text(self.run/".."/"outside","wrong")
     def test_run_collision_after_plan(self):
      c=self.ctx();self.run.mkdir()
      with self.assertRaises(FileExistsError):c.write_text(self.run/"a","wrong")
     def test_evidence_traversal_rejected(self):
      c=self.ctx()
      with self.assertRaises(ValueError):c.evidence("../escape")
     def test_evidence_absolute_rejected(self):
      c=self.ctx()
      with self.assertRaises(ValueError):c.evidence(str(self.base))
     def test_input_logical_path(self):
      c=self.ctx();self.assertEqual(c.read_input("data/a.json"),self.inp/"data"/"a.json")
     def test_input_traversal_rejected(self):
      c=self.ctx()
      with self.assertRaises(ValueError):c.read_input("../escape")
     def test_missing_evidence_stays_missing(self):
      c=self.ctx();self.assertFalse(c.evidence("missing.json").exists())
     def test_utf8_bom_writer(self):
      c=self.ctx();p=self.run/"a";c.write_text(p,"x","utf-8-sig")
      self.assertEqual(p.read_bytes(),b"\xef\xbb\xbfx")
     def test_owned_cache_manifest_update(self):
      c=self.ctx(cache_dir=self.cache,write_cache=True);m.configure_context(c);p=self.cache/"dense_cache_manifest.json"
      m.atomic_write_json(p,{"synthetic":1});m.atomic_write_json(p,{"synthetic":2})
      self.assertEqual(json.loads(p.read_text()),{"synthetic":2})
     def test_owned_cache_resume(self):
      c=self.ctx(cache_dir=self.cache,write_cache=True);c._ensure_cache()
      c2=self.ctx(run_dir=self.base/"next_run",cache_dir=self.cache,write_cache=True)
      self.assertTrue(c2._cache_owned)
     def test_changed_cache_identity_rejected(self):
      c=self.ctx(cache_dir=self.cache,write_cache=True);c._ensure_cache()
      other=self.base/"other";other.mkdir()
      with self.assertRaises(ValueError):self.ctx(input_root=other,cache_dir=self.cache,write_cache=True)
     def test_tampered_cache_owner_rejected(self):
      c=self.ctx(cache_dir=self.cache,write_cache=True);c._ensure_cache()
      (self.cache/".module2-cache-owner.json").write_text("{}")
      with self.assertRaises(ValueError):c.write_text(self.cache/"chunk","wrong")
     def test_mutable_run_target_rejected(self):
      c=self.ctx()
      with self.assertRaises(ValueError):c.publish(self.run/"a",lambda f:f.write(b"x"),True)
     def test_immutable_cache_chunk(self):
      c=self.ctx(cache_dir=self.cache,write_cache=True);p=self.cache/"chunk.npz"
      c.publish(p,lambda f:f.write(b"synthetic"))
      with self.assertRaises(FileExistsError):c.publish(p,lambda f:f.write(b"wrong"))
      self.assertEqual(p.read_bytes(),b"synthetic")
     def test_no_context_json_writer_rejected(self):
      m._ACTIVE_CONTEXT=None
      with self.assertRaises(RuntimeError):m.atomic_write_json(self.base/"a",{})
     def test_reparse_rejected(self):
      link=Path(os.environ["MODULE2_REPARSE"])
      with self.assertRaises(ValueError):self.ctx(run_dir=link/"run")
     def test_cli_help_no_writes(self):
      old=sys.argv;sys.argv=["module2","--help"]
      try:
       with self.assertRaises(SystemExit) as e,redirect_stdout(io.StringIO()):m.main()
       self.assertEqual(e.exception.code,0)
      finally:sys.argv=old
      self.assertFalse(self.run.exists())
     def test_cli_path_plan_no_writes(self):
      old=sys.argv;sys.argv=["module2","--input-root",str(self.inp),"--evidence-root",str(self.ev),"--run-dir",str(self.run),"--cache-dir",str(self.cache),"--check-paths"]
      try:
       with redirect_stdout(io.StringIO()):self.assertEqual(m.main(),0)
      finally:sys.argv=old
      self.assertFalse(self.run.exists());self.assertFalse(self.cache.exists())

     def test_library_cache_required_before_writes(self):
      c=self.ctx();old=dict(os.environ);os.environ.pop("SHROOM_MODULE2_LIBRARY_CACHE",None)
      try:
       with self.assertRaises(ValueError):c.runtime_environment()
       self.assertFalse(self.run.exists())
      finally:os.environ.clear();os.environ.update(old)
     def test_library_input_overlap_rejected(self):
      c=self.ctx();old=dict(os.environ);os.environ["SHROOM_MODULE2_LIBRARY_CACHE"]=str(self.inp)
      try:
       with self.assertRaises(ValueError):c.runtime_environment()
      finally:os.environ.clear();os.environ.update(old)
     def test_library_git_root_rejected(self):
      c=self.ctx();lib=self.base/"library";lib.mkdir();(lib/".git").write_text("synthetic")
      old=dict(os.environ);os.environ["SHROOM_MODULE2_LIBRARY_CACHE"]=str(lib)
      try:
       with self.assertRaises(ValueError):c.runtime_environment()
      finally:os.environ.clear();os.environ.update(old)
     def test_explicit_prepared_library_cache(self):
      c=self.ctx();lib=self.base/"library";lib.mkdir();old=dict(os.environ);os.environ["SHROOM_MODULE2_LIBRARY_CACHE"]=str(lib)
      try:
       c.runtime_environment()
       self.assertEqual(os.environ["HF_HOME"],str(lib))
       self.assertEqual(os.environ["HF_HUB_CACHE"],str(lib/"hub"))
       self.assertTrue((self.run/".temporary").is_dir())
      finally:os.environ.clear();os.environ.update(old)

     def test_alternate_stream_rejected(self):
      c=self.ctx()
      with self.assertRaises(ValueError):c.write_text(self.run/"a:stream","wrong")
     def test_device_path_rejected(self):
      c=self.ctx()
      with self.assertRaises(ValueError):c.write_text(self.run/"NUL","wrong")
     def test_trailing_dot_path_rejected(self):
      c=self.ctx()
      with self.assertRaises(ValueError):c.write_text(self.run/"name.","wrong")
    class Result(unittest.TestResult):
     def __init__(self):super().__init__();self.rows=[]
     def startTest(self,t):super().startTest(t);self.current={"case":t.id(),"status":"PASS"}
     def stopTest(self,t):self.rows.append(self.current);super().stopTest(t)
     def addError(self,t,e):self.current.update(status="FAIL",detail=self._exc_info_to_string(e,t));super().addError(t,e)
     def addFailure(self,t,e):self.current.update(status="FAIL",detail=self._exc_info_to_string(e,t));super().addFailure(t,e)
    result=Result();unittest.defaultTestLoader.loadTestsFromTestCase(T).run(result)
    print(json.dumps({"tests":result.testsRun,"failures":len(result.failures)+len(result.errors),"cases":result.rows,"events":events,"import_side_effects":False,"ml_imported":False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
