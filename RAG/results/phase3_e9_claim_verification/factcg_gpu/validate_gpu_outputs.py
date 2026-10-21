import argparse
from pathlib import Path
from factcg_common import validate_outputs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate a complete frozen FactCG return')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    validate_outputs(args.output, args.output.parent / 'FACTCG_GPU_REPORT.json')
    print('PASS: 561 unique scores with verified model and input provenance')
