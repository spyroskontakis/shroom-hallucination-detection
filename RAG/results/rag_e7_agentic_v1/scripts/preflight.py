"""Label-free integrity/alignment preflight before implementation or scoring."""
from e7_common import *

if __name__ == '__main__':
    guard = offline('preflight_repaired_v1')
    try:
        result = initial_preflight()
        assert not guard.events
        write_json(OUT / 'config/preflight.json', result)
        print('PASS: frozen hashes, 561 IDs, locked folds, 14/25 aligned predictors, runtime; no label projection.', flush=True)
    finally:
        guard.save()
