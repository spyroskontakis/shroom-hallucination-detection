"""Offline contract and IO tests, not model execution or metric reproduction.

Run with an externally prepared SHROOM_TEST_SCRATCH directory and -B -I -S.
All mutable fixtures are created below that directory, never in the checkout.
"""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import unittest
import uuid

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'research/shared_tools/canonical_execution_context.py').is_file())
ADAPTER = ROOT/'research/experiments/phase2_rag_features/e6_feature_extensions/v4/verification/h2_adapter_v1.py'
spec = importlib.util.spec_from_file_location('e6_v4_h2_test_adapter', ADAPTER)
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)


class H2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = A.checked_path(os.environ['SHROOM_TEST_SCRATCH'])
        A.outside_git(cls.scratch)
        if not cls.scratch.is_dir():
            raise RuntimeError('Pre-created scratch directory required')
        cls.home = cls.scratch/('h2_v4_'+uuid.uuid4().hex)
        cls.home.mkdir()
        cls.original = cls.home/'original'
        cls.temp = cls.home/'temporary'
        cls.original.mkdir()
        cls.temp.mkdir()
        cls.path = ROOT/A.DEFAULT_CONTRACT
        cls.data = json.loads(cls.path.read_text(encoding='utf-8'))
        cls.contract = A.Contract(ROOT, cls.path, A.digest(cls.path.read_bytes()))

    def context(self):
        return A.RuntimeContext(self.contract, self.original, self.home/('run_'+uuid.uuid4().hex), self.temp,
                                profile='amended', synthetic=True)

    def mutation(self, change):
        # A contract-pin mutation is deliberately measured, not silently trusted.
        # The root and raw sources stay the real reviewed repository. Contract
        # parsing is performed from a fake read-only path, without writing there.
        d = copy.deepcopy(self.data)
        change(d)
        raw = (json.dumps(d, sort_keys=True)+'\n').encode()
        old_read = Path.read_bytes
        def read(path):
            return raw if path == self.path else old_read(path)
        from unittest.mock import patch
        with patch.object(Path, 'read_bytes', read):
            with self.assertRaises((ValueError, KeyError, TypeError)):
                A.Contract(ROOT, self.path, A.digest(raw))

    def test_contract_sources(self):
        self.assertEqual(self.contract.verify_sources()['raw_artifacts'], 62)

    def test_no_missing_source_fallback(self):
        with self.assertRaises(ValueError):
            self.contract.source(A.LEGACY+'unknown.py')

    def test_wrong_external_pin(self):
        with self.assertRaises(ValueError):
            A.Contract(ROOT, self.path, '0'*64)

    def test_bad_pin_format(self):
        with self.assertRaises(ValueError):
            A.Contract(ROOT, self.path, 'unspecified')

    def test_version(self):
        self.mutation(lambda d: d.update(version='unreviewed'))

    def test_baseline(self):
        self.mutation(lambda d: d['baseline'].update(commit='0'*40))

    def test_unknown_schema(self):
        self.mutation(lambda d: d.update(extra=True))

    def test_incomplete_set(self):
        self.mutation(lambda d: d['artifacts'].pop())

    def test_duplicate_source(self):
        self.mutation(lambda d: d['artifacts'].append(d['artifacts'][0]))

    def test_duplicate_target(self):
        self.mutation(lambda d: d['artifacts'][1].update(current_path=d['artifacts'][0]['current_path']))

    def test_source_escape(self):
        self.mutation(lambda d: d['artifacts'][0].update(current_path='../outside'))

    def test_raw_source_identity(self):
        self.mutation(lambda d: d['artifacts'][0].update(current_sha256='0'*64))

    def test_derived_source_identity(self):
        self.mutation(lambda d: d['artifacts'][0].update(adapted_source_sha256='0'*64))

    def test_blob_identity(self):
        self.mutation(lambda d: d['artifacts'][0]['h1'].update(git_blob='0'*40))

    def test_source_size(self):
        self.mutation(lambda d: d['artifacts'][0]['h1'].update(size_bytes=0))

    def test_adapter_identity(self):
        self.mutation(lambda d: d['adapter'].update(sha256='0'*64))

    def test_shared_identity(self):
        self.mutation(lambda d: d['adapter'].update(shared_validator_sha256='0'*64))

    def test_symbol_identity(self):
        def change(d):
            x = next(x for x in d['artifacts'] if x['scientific_symbols'])
            x['scientific_symbols'][next(iter(x['scientific_symbols']))] = '0'*64
        self.mutation(change)

    def test_asset_binding_schema(self):
        self.mutation(lambda d: d.update(asset_directories=['../outside']))

    def test_alias_scope(self):
        self.mutation(lambda d: d['historical_aliases'].update({'outside':'../outside'}))

    def test_strict_json(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.contract.shared.strict_json(raw)

    def test_profiles(self):
        self.assertEqual(len(self.contract.expected_originals('diagnosis')), 1896)
        self.assertEqual(len(self.contract.expected_originals('amended')), 3412)
        with self.assertRaises(ValueError):
            self.contract.expected_originals('automatic')

    def test_original_missing_before_writes(self):
        run = self.home/('never_created_'+uuid.uuid4().hex)
        with self.assertRaises(ValueError):
            A.RuntimeContext(self.contract, self.original, run, self.temp, profile='amended')
        self.assertFalse(run.exists())

    def test_original_is_not_public_h1(self):
        run = self.home/('no_h1_fallback_'+uuid.uuid4().hex)
        with self.assertRaises(ValueError):
            A.RuntimeContext(self.contract, ROOT, run, self.temp, profile='amended')
        self.assertFalse(run.exists())

    def test_path_rejections(self):
        for path in ('relative', str(self.home/'..'/'escape'), str(self.home/'NUL.txt'), str(self.home/'unsafe:stream'), str(self.home/'tail.')):
            with self.subTest(path=path), self.assertRaises(ValueError):
                A.checked_path(path)

    def test_overlapping_roots(self):
        with self.assertRaises(ValueError):
            A.RuntimeContext(self.contract, self.original, self.original/'out', self.temp, profile='amended', synthetic=True)

    def test_repository_output(self):
        with self.assertRaises(ValueError):
            A.RuntimeContext(self.contract, self.original, ROOT/'never_created', self.temp, profile='amended', synthetic=True)

    def test_existing_unowned_run(self):
        with self.assertRaises(ValueError):
            A.RuntimeContext(self.contract, self.original, self.temp, self.home, profile='amended', synthetic=True)
        run = self.home/('unowned_'+uuid.uuid4().hex)
        run.mkdir()
        with self.assertRaises(ValueError):
            A.RuntimeContext(self.contract, self.original, run, self.temp, profile='amended', synthetic=True)

    def test_bindings(self):
        c = self.context()
        self.assertEqual(c.binding('ROOT','execution'), self.original)
        self.assertEqual(c.binding('V4','execution'), c.run)
        self.assertEqual(c.binding('HERE','execution'), c.run/'execution')
        with self.assertRaises(ValueError):
            c.binding('AUTO','execution')

    def test_source_resolution(self):
        c = self.context()
        old = A.LEGACY+'execution/common.py'
        self.assertEqual(c.io_path(c.run/'execution/common.py'), self.contract.source(old))
        with c.historical_reads(), self.assertRaises(ValueError):
            c.io_path(c.run/'execution/common.py')

    def test_scientific_entries_not_imported(self):
        c = self.context()
        for old in ('execution/extract.py','execution/evaluate.py','compatibility_analysis/reproduce_minimal.py'):
            with self.subTest(old=old), self.assertRaises(ValueError):
                c.load(A.LEGACY+old, entry=True)
        with self.assertRaises(ValueError):
            c.prepare()

    def test_actual_libraries_and_synthetic_json(self):
        c = self.context()
        before = set(sys.modules)
        common = c.load(A.LEGACY+'execution/common.py')
        v4 = c.load(A.LEGACY+'scripts/v4_common.py')
        structure = c.load(A.LEGACY+'scripts/structure.py')
        self.assertEqual(common.ROOT, self.original)
        self.assertEqual(common.HERE, c.run/'execution')
        self.assertEqual(v4.OUT, c.run)
        self.assertEqual(v4.ROOT, self.original)
        c.run.mkdir()
        p = c.run/'synthetic.json'
        v4.write_json(p, {'synthetic':True})
        self.assertEqual(v4.read_json(p), {'synthetic':True})
        with self.assertRaises((ValueError, FileExistsError)):
            v4.write_json(p, {'overwrite':True})
        self.assertEqual(structure.contracts(), 'PASS')
        self.assertFalse({'torch','transformers','bert_score','sentence_transformers'} & (set(sys.modules)-before))

    def test_module_finder(self):
        c = self.context()
        f = A.ModuleFinder(c)
        old = {name:sys.modules.get(name) for name in f.aliases}
        self.assertTrue(all(x is None for x in old.values()))
        sys.meta_path.insert(0, f)
        try:
            import common, v4_common, structure
            self.assertEqual(common.V4, c.run)
            self.assertEqual(v4_common.OUT, c.run)
            self.assertEqual(structure.contracts(), 'PASS')
        finally:
            sys.meta_path.remove(f)
            for name in f.aliases:
                sys.modules.pop(name, None)

    def test_writer_scope(self):
        c = self.context()
        for p in (self.original/'output', ROOT/'output', self.home/'outside'):
            with self.subTest(path=p.name), self.assertRaises(ValueError):
                c.io_path(p,'w')
        with self.assertRaises(ValueError):
            c.io_path(c.run/'execution/common.py','w')
        self.assertEqual(c.io_path(c.run/'safe.json','x'), c.run/'safe.json')

    def test_policy_denials(self):
        c = self.context()
        for event,args in [('socket.connect',()),('subprocess.Popen',('python',['python'],None,{})),('os.mkdir',(str(ROOT/'no_write'),0o777,-1)),('os.symlink',(str(c.run/'a'),str(c.run/'b'),-1))]:
            with self.subTest(event=event), self.assertRaises(ValueError):
                c.policy(event,args)
        c.policy('open',(str(self.contract.source(A.LEGACY+'scripts/structure.py')),'r',0))

    def test_git_command_rejection(self):
        c = self.context()
        with self.assertRaises(ValueError):
            c.original_git(['git','reset','--hard'])
        self.assertIsNone(c.approved_git)

    def test_inventory(self):
        c = self.context()
        c.run.mkdir()
        (c.run/'execution').mkdir()
        (c.run/'execution/synthetic.json').write_text('{}')
        refs = sorted(c.inventory(c.run/'execution','*','glob'))
        names = [x.relative_to(c.run/'execution').as_posix() for x in refs]
        self.assertIn('common.py', names)
        self.assertIn('synthetic.json', names)
        raw = next(x for x in refs if x.name == 'common.py')
        self.assertEqual(c.io_path(raw), self.contract.source(A.LEGACY+'execution/common.py'))

    def test_raw_and_derived_syntax(self):
        for old,x in self.contract.artifacts.items():
            if old.endswith('.py'):
                with self.subTest(source=old):
                    raw = self.contract.source(old).read_bytes()
                    derived = A.adapted_source(raw,old)
                    ast.parse(raw)
                    ast.parse(derived)
                    self.assertEqual(A.digest(derived), x['adapted_source_sha256'])

    def test_scientific_ast(self):
        checks = {'execution/evaluate.py':('metric','paired'), 'execution/common.py':('scorer',), 'scripts/structure.py':('normalize','tokens','numbers','negated','features','contracts')}
        for rel,names in checks.items():
            old = A.LEGACY+rel
            raw = self.contract.source(old).read_bytes()
            raw_nodes = A._scientific_nodes(raw)
            new_nodes = A._scientific_nodes(A.adapted_source(raw, old))
            for name in names:
                with self.subTest(source=rel, symbol=name):
                    self.assertEqual(raw_nodes[name],new_nodes[name])

    def test_plan_only(self):
        from contextlib import redirect_stdout
        from io import StringIO
        output = StringIO()
        with redirect_stdout(output):
            code = A.main(['--expected-sha256', self.contract.pin])
        self.assertEqual(code,0)
        d = json.loads(output.getvalue())
        self.assertEqual(d['mode'],'PLAN_ONLY')
        self.assertEqual(d['created_files'],0)
        self.assertEqual(d['runtime_status'],'NOT_RUNTIME_VERIFIED')

    def test_execute_requires_explicit_inputs(self):
        from unittest.mock import patch
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            A.main(['--expected-sha256', self.contract.pin, '--execute', '--entry',A.LEGACY+'execution/extract.py'])

    def test_entire_scientific_projection(self):
        for old in self.contract.artifacts:
            if old.endswith('.py'):
                with self.subTest(source=old):
                    raw = self.contract.source(old).read_bytes()
                    self.assertEqual(A.scientific_projection(raw), A.scientific_projection(A.adapted_source(raw,old)))

    def test_projection_detects_algorithm_change(self):
        raw = b'def metric(a, b):\n    return a + b\n'
        self.assertNotEqual(A.scientific_projection(raw), A.scientific_projection(raw.replace(b'a + b',b'a - b')))

    def test_no_existing_overwrite(self):
        c = self.context()
        c.run.mkdir()
        p = c.run/'prior.json'
        p.write_text('historical')
        with self.assertRaises(ValueError):
            c.io_path(p,'w')
        with self.assertRaises(ValueError):
            c.io_path(p,'a')
        self.assertEqual(p.read_text(),'historical')

    def test_no_historical_source_write(self):
        c = self.context()
        ref = A.SourceRef(c, A.LEGACY+'scripts/structure.py')
        with self.assertRaises(ValueError):
            c.io_path(ref,'x')

    def test_explicit_original_revalidation(self):
        c = self.context()
        logical = 'synthetic/'+uuid.uuid4().hex+'.json'
        p = self.original/logical
        p.parent.mkdir(exist_ok=True)
        p.write_bytes(b'original')
        c.expected[logical] = A.digest(b'original')
        self.assertEqual(c.original_path(logical),p)
        p.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            c.original_path(logical)

    def test_fresh_results_not_historical_fallback(self):
        c = self.context()
        self.assertEqual(c.io_path(c.run/'evaluation/metrics.json'), c.run/'evaluation/metrics.json')

    def test_required_model_and_revision_identities(self):
        model = json.loads(self.contract.source(self.data['model_requirement_record']).read_text(encoding='utf-8'))
        expected = self.contract.expected_originals('amended')
        for asset in model['model_files'].values():
            self.assertEqual(expected[asset['path']], asset['sha256'])
        self.assertEqual(expected[model['cache_ref_path']],model['cache_ref_sha256'])
        self.mutation(lambda d: d.update(model_requirement_record='unknown.json'))

    def test_actual_installed_io_guard(self):
        c = self.context()
        c.run.mkdir()
        current = [c]
        def guard(event,args):
            if current[0] is not None:
                current[0].policy(event,args)
        sys.addaudithook(guard)
        try:
            # Uses actual rewritten library source and actual Python audit events.
            common = c.load(A.LEGACY+'execution/common.py')
            p = c.run/'guarded_synthetic.json'
            common.write(p, {'synthetic':True})
            self.assertEqual(common.read(p), {'synthetic':True})
            with self.assertRaises(ValueError):
                (self.home/'forbidden.txt').open('x')
            with self.assertRaises(ValueError):
                common.write(p, {'overwrite':True})
        finally:
            current[0] = None


if __name__ == '__main__':
    unittest.main(verbosity=2)
