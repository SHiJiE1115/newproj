"""Packet-root input resolution and compressed/canonical content checks."""
import gzip
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT/'DATA_MANIFEST.json').read_text(encoding='utf-8'))
CACHE = {}


def digest(raw): return hashlib.sha256(raw).hexdigest()
def packet_path(name):
    path = (ROOT/name).resolve()
    assert path.is_relative_to(ROOT) and path != ROOT
    return path


def data(key):
    if key in CACHE: return CACHE[key]
    record = MANIFEST['datasets'][key]
    raw = packet_path(record['file']).read_bytes()
    assert len(raw) == record['compressed_bytes'] and digest(raw) == record['compressed_sha256']
    assert record['canonical_bytes'] <= 32*1024*1024
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f: decoded = f.read(record['canonical_bytes']+1)
    assert len(decoded) == record['canonical_bytes'] and digest(decoded) == record['canonical_sha256']
    result = json.loads(decoded)
    CACHE[key] = result
    return result


def check_static_files():
    manifest = json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
    for record in manifest['files']:
        raw = packet_path(record['file']).read_bytes()
        assert len(raw) == record['bytes'] and digest(raw) == record['sha256'], record['file']
    for record in MANIFEST['analytic_proof_texts']:
        raw = packet_path(record['file']).read_bytes()
        assert len(raw) == record['bytes'] and digest(raw) == record['sha256']
    return len(manifest['files'])


def words(task): return [w for w in range(16) if (task[0] | task[1])>>w & 1]
def transform(w, perm, xor=0): return sum(((w>>q)&1)<<perm[q] for q in range(4)) ^ xor
def trace(tree, w):
    seen = []
    while isinstance(tree, list):
        assert len(tree) == 3
        q = tree[0]; assert type(q) is int and q in range(4) and q not in seen
        seen.append(q); tree = tree[1+((w>>q)&1)]
    return tree, sum(1<<q for q in seen), seen
