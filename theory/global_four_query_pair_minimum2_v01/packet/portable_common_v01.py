"""Whole-object provenance normalization. No mathematical keys are discarded."""
import copy
import hashlib
import json
from pathlib import Path


def raw_hash(b):
    return hashlib.sha256(b).hexdigest()


def encoded(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def save(p, v):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')


def pin(p):
    p = Path(p)
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': raw_hash(b)}


def pathkey(s):
    return str(s).replace('\\', '/').lower()


class Canon:
    """Resolve supplied references; immutable unknown origin metadata stays opaque.

    Dynamic JSON references use SHA of the ENTIRE recursively normalized object.
    Raw stable files preserve their bytes/SHA. Execution PID and terminal pins
    are replaced by declared phase roles only after receipt validation outside
    this class. This is provenance comparison, not a mathematical validator.
    """

    def __init__(self, packet, manifest, actual=None, aliases=None):
        self.packet = Path(packet)
        self.manifest = manifest
        self.actual = actual or {}
        self.aliases = aliases or {}
        self.rows = {r['role']: r for r in manifest['files']}
        self.paths = {}
        self.memo = {}
        for role, row in self.rows.items():
            self.paths[pathkey(row['origin_path'])] = role
            self.paths[pathkey(self.packet / row['file'])] = role
        for role, p in self.actual.items():
            self.paths[pathkey(p)] = role
        for p, role in self.aliases.items():
            self.paths[pathkey(p)] = role

    def location(self, role):
        return Path(self.actual.get(role, self.packet / self.rows[role]['file']))

    def object(self, role):
        return self.object_at(role, self.location(role))

    def object_at(self, role, f):
        key = (role, str(f))
        if key not in self.memo:
            self.memo[key] = self.norm(read(f))
        return self.memo[key]

    def referenced_file(self, role, literal_path):
        for p, alias_role in self.aliases.items():
            if pathkey(p) == pathkey(literal_path):
                assert role == alias_role
                return Path(p)
        if role in self.actual and pathkey(literal_path) == pathkey(self.actual[role]):
            return Path(self.actual[role])
        return self.packet / self.rows[role]['file']

    def norm(self, obj):
        if isinstance(obj, list):
            return [self.norm(x) for x in obj]
        if isinstance(obj, str):
            if raw_hash(obj.encode('utf-8')) == 'e703022664135ea6d811faef48762e66a74ac29b97e1c0fe0881c17e9ceb263a':
                return 'origin-private://sealed-P1-location'
            role = self.paths.get(pathkey(obj))
            return '@artifact/' + role if role else obj
        if not isinstance(obj, dict):
            return obj
        # These exact four-key process summaries occur only in composed output.
        if set(obj) == {'phase', 'pid', 'actual_exit_code', 'terminal'}:
            assert obj['actual_exit_code'] == 0 and type(obj['pid']) is int
            t = obj['terminal']
            assert isinstance(t, dict) and set(t) == {'path', 'bytes', 'sha256'}
            role = self.paths.get(pathkey(t['path']))
            assert role == 'terminal/' + obj['phase'], (obj['phase'], role)
            f = self.referenced_file(role, t['path'])
            assert {k: pin(f)[k] for k in ('bytes', 'sha256')} == {k: t[k] for k in ('bytes', 'sha256')}
            receipt = read(f)
            assert receipt['pid'] == obj['pid'] and receipt['actual_exit_code'] == 0
            assert receipt['timed_out'] is False
            return {'phase': obj['phase'], 'pid': '@process/' + obj['phase'],
                    'actual_exit_code': 0,
                    'terminal': {'path': '@artifact/' + role, 'bytes': '@execution-metadata',
                                 'sha256': '@verified-actual-zero-exit/' + obj['phase']}}
        if {'path', 'bytes', 'sha256'} <= set(obj):
            role = self.paths.get(pathkey(obj['path']))
            if role:
                f = self.referenced_file(role, obj['path'])
                p = pin(f)
                claimed = {k: obj[k] for k in ('bytes', 'sha256')}
                observed = {k: p[k] for k in ('bytes', 'sha256')}
                if observed != claimed:
                    # Explicit origin-metadata bridge, never a raw-original check.
                    bridge = self.rows[role].get('origin_metadata_derivative')
                    assert role == 'iteration441/ACCEPTANCE_V01.json' and bridge
                    assert claimed == {'bytes': bridge['origin_bytes'], 'sha256': bridge['origin_sha256']}
                    assert observed == {k: self.rows[role][k] for k in ('bytes', 'sha256')}
                    assert f == self.packet / self.rows[role]['file']
                    assert bridge['only_one_path_string_literal_changed_all_other_raw_bytes_exact'] is True
                row = self.rows[role]
                rest = {k: self.norm(v) for k, v in obj.items() if k not in ('path', 'bytes', 'sha256')}
                if row.get('dynamic_json'):
                    v = encoded(self.object_at(role, f))
                    return {'path': '@artifact/' + role, 'bytes': len(v), 'sha256': raw_hash(v),
                            **rest, '_reference_encoding': 'whole-normalized-JSON-v1'}
                assert len(f.read_bytes()) == row['bytes'] and raw_hash(f.read_bytes()) == row['sha256']
                return {'path': '@artifact/' + role, 'bytes': obj['bytes'], 'sha256': obj['sha256'], **rest}
        return {k: self.norm(v) for k, v in obj.items()}


def shape(v):
    counts = {'dict': 0, 'list': 0, 'str': 0, 'int': 0, 'bool': 0, 'float': 0, 'null': 0}
    def walk(x):
        if isinstance(x, dict):
            counts['dict'] += 1
            for y in x.values(): walk(y)
        elif isinstance(x, list):
            counts['list'] += 1
            for y in x: walk(y)
        elif x is None: counts['null'] += 1
        elif type(x) is bool: counts['bool'] += 1
        elif type(x) is int: counts['int'] += 1
        elif type(x) is float: counts['float'] += 1
        elif isinstance(x, str): counts['str'] += 1
        else: raise TypeError(type(x))
    walk(v)
    return counts


def diff(a, b, p=''):
    if type(a) is not type(b): return (p, 'type', type(a).__name__, type(b).__name__)
    if isinstance(a, dict):
        if a.keys() != b.keys(): return (p, 'keys', list(a), list(b))
        for k in a:
            d = diff(a[k], b[k], p + '/' + str(k))
            if d: return d
    elif isinstance(a, list):
        if len(a) != len(b): return (p, 'length', len(a), len(b))
        for i, (x, y) in enumerate(zip(a, b)):
            d = diff(x, y, p + '/' + str(i))
            if d: return d
    elif a != b: return (p, 'value', a, b)
    return None
