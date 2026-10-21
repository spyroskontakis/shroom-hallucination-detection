"""Locked-run verification, split auditing and fixed E7 descriptive statistics."""
import numpy as np
from scipy.stats import spearmanr, binomtest
from e7_common import OUT, E6, FOLDS, now, sha, read_json, write_json, verify_integrity


def verify_evaluation_freeze():
    protocol = verify_integrity()
    frozen = read_json(OUT / 'config/evaluation_freeze.json')
    assert frozen['protocol_sha256'] == protocol['protocol_sha256']
    assert frozen['protocol_freeze_sha256'] == sha(OUT / 'config/protocol_freeze.json')
    assert frozen['protected_sha256'] == protocol['protected_sha256']
    assert sha(FOLDS) == frozen['fold_sha256']
    for section in ('implementation_sha256', 'config_sha256'):
        for p,h in frozen[section].items():
            assert sha(OUT / p) == h, f'Frozen execution input changed: {p}'
    return frozen


def metric(frame, name):
    y = frame.p_hallucination.to_numpy(float)
    p = frame[name].to_numpy(float)
    truth = frame.label_bin.to_numpy(int)
    assert len(p) and np.isfinite(p).all() and ((0<=p)&(p<=1)).all()
    rounded = np.round(p,12)
    rho = None
    if len(p)>1 and len(np.unique(y))>1 and len(np.unique(rounded))>1:
        rho = float(spearmanr(y,rounded).statistic)
    correct = int(((p>=.5).astype(int)==truth).sum())
    return {'n':len(p),'correct':correct,'accuracy':correct/len(p),'spearman':rho}


def paired(frame, baseline):
    c7 = (frame.E7.to_numpy()>=.5).astype(int)==frame.label_bin.to_numpy(int)
    cb = (frame[baseline].to_numpy()>=.5).astype(int)==frame.label_bin.to_numpy(int)
    corrected, regressed = ~cb & c7, cb & ~c7
    b,c = int(corrected.sum()),int(regressed.sum())
    d = c7.astype(int)-cb.astype(int)
    rng = np.random.default_rng(42)
    boots = np.array([d[rng.integers(0,len(d),len(d))].mean() for _ in range(10000)])
    return {'corrections':b,'regressions':c,'net_correct':b-c,'accuracy_difference':float(d.mean()),
            'mcnemar_exact_two_sided_p':float(binomtest(b,b+c,.5).pvalue) if b+c else 1.0,
            'paired_bootstrap':{'replicates':10000,'seed':42,'paired_rows':len(d),
                                'percentile_95_ci':np.quantile(boots,[.025,.975]).tolist()},
            'corrected_ids':frame.loc[corrected,'canonical_id'].tolist(),
            'regressed_ids':frame.loc[regressed,'canonical_id'].tolist(),
            'changes_by_route':{route:{'corrections':int((corrected & (frame.route==route)).sum()),
                                      'regressions':int((regressed & (frame.route==route)).sum())}
                                for route in sorted(frame.route.unique())}}


def audited_cv(evaluator, frame, features, path, real_factory, parameters):
    """Keep accepted run_cv byte-identical; observe/validate its estimator boundary."""
    instances = []

    class AuditedEstimator:
        def __init__(self, **kwargs):
            self.fold = len(instances)+1
            assert self.fold <= 5
            self.train = frame.loc[frame.fold_id != self.fold]
            self.valid = frame.loc[frame.fold_id == self.fold]
            self.model = real_factory(**kwargs)
            assert self.model.get_params() == parameters
            self.fitted = False
            self.predicted = False
            instances.append(self)

        def fit(self, x, y):
            assert not self.fitted
            assert np.array_equal(x,self.train[features].to_numpy(float))
            assert np.array_equal(y,self.train.p_hallucination.to_numpy(float))
            assert not set(self.train.canonical_id) & set(self.valid.canonical_id)
            write_json(OUT / f'evaluation/fits/{path}_fold{self.fold}_started.json', {
                'started_utc':now(),'path':path,'fold_id':self.fold,'train_n':len(self.train),
                'validation_n':len(self.valid),'train_ids':self.train.canonical_id.tolist(),
                'validation_ids':self.valid.canonical_id.tolist(),'features':features,
                'fit_inputs_match_outer_train':True,'validation_rows_excluded_from_fit':True})
            self.model.fit(x,y)
            self.fitted = True
            return self

        def predict(self,x):
            assert self.fitted and not self.predicted
            assert np.array_equal(x,self.valid[features].to_numpy(float))
            p = self.model.predict(x)
            self.predicted = True
            assert len(p)==len(self.valid) and np.isfinite(p).all()
            write_json(OUT / f'evaluation/fits/{path}_fold{self.fold}_completed.json', {
                'completed_utc':now(),'path':path,'fold_id':self.fold,'predicted_rows':len(p),
                'fit_count':1,'predict_count':1,'validation_inputs_match':True})
            print(f'{path} fold {self.fold}/5 fitted and predicted; no E7 score computed yet.',flush=True)
            return p

    original_factory = evaluator.RandomForestRegressor
    evaluator.RandomForestRegressor = AuditedEstimator
    try:
        predictions = evaluator.run_cv(frame,features)
    finally:
        evaluator.RandomForestRegressor = original_factory
    assert len(instances)==5 and all(m.fitted and m.predicted for m in instances)
    assert predictions.canonical_id.tolist()==frame.canonical_id.tolist()
    assert predictions.fold_id.tolist()==frame.fold_id.tolist()
    return predictions
