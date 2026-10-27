"""One-time candidate-only diagnostic transformation; refuses a second application."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert not (ROOT / '.git').exists(), 'Candidate must have no Git history'
    ledger = ROOT / 'manifests/public_release_transformations.json'
    assert not ledger.exists(), 'Already transformed; do not repeat'
    changes = []
    prepared = []
    for name in ('minimal_current.json', 'minimal_pinned.json'):
        rel = 'RAG/results/rag_e6_v4/compatibility_analysis/' + name
        old = (ROOT / rel).read_bytes()
        data = json.loads(old)
        assert 'public_release_transform' not in data
        removed = []
        for key, entry in data['sources'].items():
            text = entry.pop('source')
            version = data['versions']['transformers'] if key in ('tokenizer_class', 'encode') else data['versions']['bert-score']
            if key == 'tokenizer_class':
                url = f'https://github.com/huggingface/transformers/blob/v{version}/src/transformers/models/deberta/tokenization_deberta.py'
            elif key == 'encode':
                url = f'https://github.com/huggingface/transformers/blob/v{version}/src/transformers/tokenization_utils_base.py'
            else:
                filename = 'scorer.py' if key.startswith('scorer_') else 'utils.py'
                url = f'https://github.com/Tiiiger/bert_score/blob/v{version}/bert_score/{filename}'
            entry.update(source_text_sha256=sha(text.encode()), source_text_bytes=len(text.encode()), upstream_source=url,
                         source_omitted_reason='Retain version, location and hashes instead of embedded third-party source.')
            removed.append(dict(json_pointer='/sources/' + key + '/source', utf8_bytes=len(text.encode()), sha256=sha(text.encode()), upstream_source=url))
        if 'traceback' in data:
            data['traceback'] = '\n'.join(line for line in data['traceback'].splitlines()
                if line.startswith('Traceback') or line.lstrip().startswith('File ') or (line and not line.startswith(' '))) + '\n'
            removed.append(dict(json_pointer='/traceback', change='Remove code/caret excerpts; retain frame locations and exception text.'))
        for index, frame in enumerate(data.get('frames', [])):
            if 'source' in frame:
                text = frame.pop('source')
                frame['source_text_sha256'] = sha(text.encode())
                removed.append(dict(json_pointer=f'/frames/{index}/source', sha256=sha(text.encode()), utf8_bytes=len(text.encode())))
        data['public_release_transform'] = dict(description='Source excerpts replaced with upstream references. Existing sha256 fields remain historical hashes, not hashes of this derivative.', original_file_sha256=sha(old))
        new = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
        prepared.append((rel, new))
        changes.append(dict(path=rel, original_sha256=sha(old), new_sha256=sha(new), removed=removed))
    for rel, new in prepared:
        (ROOT / rel).write_bytes(new)
    ledger.write_text(json.dumps(changes, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
