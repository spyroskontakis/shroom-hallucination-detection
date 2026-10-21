"""Import-only diagnostic: no datasets, feature scoring, router or estimator fit."""
from e7_common import *

if __name__ == '__main__':
    guard = offline('import_diagnostic')
    try:
        import numpy
        print('numpy imported; blocked events:', len(guard.events), flush=True)
        if not guard.events:
            from sklearn.ensemble import RandomForestRegressor
            print('sklearn.ensemble imported; blocked events:', len(guard.events), flush=True)
        # Do not proceed to initial_preflight, data loading, or fitting.
        print('STOP: import-only diagnostic complete', flush=True)
    finally:
        guard.save()
