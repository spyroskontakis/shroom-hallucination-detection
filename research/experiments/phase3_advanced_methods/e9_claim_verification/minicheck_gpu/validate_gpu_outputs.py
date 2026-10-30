"""Require a complete successful GPU return, including its machine-readable report."""
import argparse
from pathlib import Path
from gpu_common import validate_outputs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    rows = validate_outputs(args.output, args.output.parent / 'MINICHECK_GPU_REPORT.json')
    print(f'PASS: {len(rows)} unique frozen claims')
