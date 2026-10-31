"""Validate the portable input without importing ML dependencies."""
from gpu_common import validate_inputs

if __name__ == '__main__':
    m, rows = validate_inputs()
    print(f"PASS: {m['sample_count']} samples; {len(rows)} claims; "
          f"SHA256={m['package_sha256']['minicheck_inputs.jsonl']}")
