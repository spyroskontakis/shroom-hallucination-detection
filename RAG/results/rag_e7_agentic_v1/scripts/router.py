"""Frozen median-threshold controller; no labels, model scores or fitting here."""
import math
import numpy as np
import pandas as pd

OBSERVATIONS = ('evidence_available', 'top1_cosine')
USE = 'USE_EXTERNAL_EVIDENCE'
FALLBACK = 'FALLBACK_TO_BASE'


def validate_observation(row):
    if set(row) != set(OBSERVATIONS):
        raise ValueError('Router accepts exactly evidence_available and top1_cosine')
    available = row['evidence_available']
    if available not in (0, 1, False, True):
        raise ValueError('Invalid evidence flag')
    score = row['top1_cosine']
    if available:
        if score is None or not math.isfinite(float(score)) or not -1.000000000001 <= float(score) <= 1.000000000001:
            raise ValueError('Invalid available top1 cosine')
    elif score is not None and not math.isnan(float(score)):
        raise ValueError('Unavailable top1 cosine must be missing')
    return bool(available), float(score) if available else None


def fit_threshold(observations):
    scores = []
    for row in observations:
        available, score = validate_observation(row)
        if available:
            scores.append(score)
    return float(np.quantile(scores, .5, method='linear')) if scores else None


def choose_route(observation, threshold):
    available, score = validate_observation(observation)
    if threshold is not None and (not math.isfinite(float(threshold)) or not -1.000000000001 <= threshold <= 1.000000000001):
        raise ValueError('Invalid threshold')
    return USE if available and threshold is not None and score >= threshold else FALLBACK


def finish_prediction(route, predictions):
    if route not in (USE, FALLBACK) or set(predictions) != {'E3', 'E6'}:
        raise ValueError('Invalid route or prediction schema')
    for p in predictions.values():
        if not math.isfinite(float(p)) or not 0 <= p <= 1:
            raise ValueError('Predictions must be finite in [0,1]')
    return {'prediction': float(predictions['E6' if route == USE else 'E3']),
            'decision_count': 1,
            'states': ['START', 'RETRIEVE', 'ASSESS_EVIDENCE', route, 'PREDICT', 'END']}


def plan_routes(metadata, signals):
    if set(metadata.columns) != {'canonical_id', 'fold_id', 'task'}:
        raise ValueError('Only ID/fold/task metadata accepted')
    expected = {'canonical_id', 'evidence_available', 'candidate_count', 'selected_sense_count',
                'top1_cosine', 'top2_cosine', 'top1_minus_top2'}
    if set(signals.columns) != expected:
        raise ValueError('Unexpected retrieval audit schema')
    if metadata.canonical_id.duplicated().any() or signals.canonical_id.duplicated().any():
        raise ValueError('Duplicate canonical IDs')
    if metadata.canonical_id.tolist() != signals.canonical_id.tolist():
        raise ValueError('Retrieval and canonical order mismatch')
    if set(metadata.fold_id) != {1,2,3,4,5}:
        raise ValueError('Expected exactly five locked folds')
    all_rows = metadata.reset_index(drop=True).join(signals.drop(columns='canonical_id').reset_index(drop=True))
    chunks, details = [], {}
    for fold in range(1,6):
        train = all_rows.loc[all_rows.fold_id != fold]
        valid = all_rows.loc[all_rows.fold_id == fold]
        threshold = fit_threshold(train[list(OBSERVATIONS)].to_dict('records'))
        if threshold is None:
            raise ValueError('Missing training-evidence threshold: STOP')
        details[str(fold)] = {'threshold': threshold, 'quantile': .5, 'method':'linear',
                              'train_ids':train.canonical_id.tolist(),
                              'train_evidence_ids':train.loc[train.evidence_available==1,'canonical_id'].tolist(),
                              'validation_ids':valid.canonical_id.tolist()}
        out = valid[['canonical_id','fold_id','task','evidence_available','top1_cosine']].copy()
        out['threshold'] = threshold
        out['route'] = [choose_route(r, threshold) for r in valid[list(OBSERVATIONS)].to_dict('records')]
        out['decision_count'] = 1
        chunks.append(out)
    result = pd.concat(chunks).sort_index().reset_index(drop=True)
    assert result.canonical_id.tolist() == metadata.canonical_id.tolist()
    assert (result.decision_count == 1).all()
    assert (result.loc[result.evidence_available==0,'route'] == FALLBACK).all()
    return result, details
