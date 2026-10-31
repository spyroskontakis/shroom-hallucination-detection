from factcg_common import validate_inputs

if __name__ == '__main__':
    m, rows = validate_inputs()
    print(f"PASS: {len(rows)} canonical input rows; SHA256={m['package_sha256']['factcg_inputs.jsonl']}")
