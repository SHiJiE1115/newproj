#!/usr/bin/env python3
"""Check the pinned review ZIP and optionally extract it, using Python 3.10+.

This checks download bytes and listed members, not mathematical correctness,
licensing, author identity, or the truth of archived execution statements.
No network, package installation, subprocess, or mathematical verifier is used.
Obtain this script and its expected hashes from the intended release. Checksums
are integrity commitments, not a publisher signature. When extracting, use a
parent directory that other processes will not modify during this operation.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import time
import unicodedata
import zipfile


# The publisher must fill these three release-specific values before delivery.
ARCHIVE_SHA256 = '6d67d683e6b1df885df2c20f4157a11d7f71765ea219f06f9d32d4017b1693e8'
ARCHIVE_BYTES = 1253960690
OUTER_MANIFEST_SHA256 = '92636a122d81855b28d61761a353ee402b872440eaf6df96b09afae37919089d'

CANDIDATE_MANIFEST_SHA256 = 'd863b8d0f090091620dfb61e4094b9803ae3871d698a682166d5060469fba929'
CANDIDATE_MANIFEST_BYTES = 1414318
CANDIDATE_LISTED_FILES = 5568
CANDIDATE_FILES = 5569
CANDIDATE_BYTES = 1491310855
MAX_EXPANDED_BYTES = 2 * 1024**3
MAX_MEMBERS = 10000
MAX_MANIFEST_BYTES = 8 * 1024**2
BLOCK_BYTES = 1024**2
SHA256_RE = re.compile(r'[0-9a-f]{64}\Z')
WINDOWS_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'} | {
    prefix + suffix
    for prefix in ('COM', 'LPT')
    for suffix in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '\u00b9', '\u00b2', '\u00b3')
}


class VerificationError(Exception):
    pass


def require(condition, message):
    # Do not use assert: integrity checks must survive python -O.
    if not condition:
        raise VerificationError(message)


def valid_sha(value):
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def safe_name(name):
    require(isinstance(name, str) and bool(name), 'empty or non-string member path')
    require(not any(ord(c) < 32 or ord(c) == 127 for c in name), 'control character in path')
    require(not any(c in name for c in '\\:<>"|?*'), 'nonportable path character')
    path = PurePosixPath(name)
    require(not path.is_absolute() and path.as_posix() == name, 'noncanonical relative path')
    require(bool(path.parts) and all(p not in ('', '.', '..') for p in path.parts),
            'unsafe path component')
    for part in path.parts:
        require(not part.endswith((' ', '.')), 'Windows trailing dot or space in path')
        require(part.split('.', 1)[0].upper() not in WINDOWS_RESERVED, 'Windows reserved path')
    return name


def path_key(name):
    return unicodedata.normalize('NFC', name).casefold()


def check_path_set(names):
    keys = set()
    for name in names:
        safe_name(name)
        key = path_key(name)
        require(key not in keys, 'duplicate or case/Unicode-alias member path')
        keys.add(key)
    for key in keys:
        parts = key.split('/')
        require(all('/'.join(parts[:i]) not in keys for i in range(1, len(parts))),
                'file/directory prefix conflict')


def object_pairs(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, 'duplicate JSON object key')
        out[key] = value
    return out


def invalid_constant(value):
    raise VerificationError('nonfinite JSON constant: ' + value)


def strict_json(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=object_pairs,
                      parse_constant=invalid_constant)


def stream_hash(stream, limit):
    digest = hashlib.sha256()
    size = 0
    while True:
        block = stream.read(BLOCK_BYTES)
        if not block:
            break
        size += len(block)
        require(size <= limit, 'stream exceeds its declared byte limit')
        digest.update(block)
    return size, digest.hexdigest()


def load_manifest(archive, info, expected_sha):
    require(info.file_size <= MAX_MANIFEST_BYTES, 'manifest exceeds size limit')
    with archive.open(info, 'r') as source:
        raw = source.read(MAX_MANIFEST_BYTES + 1)
    require(len(raw) == info.file_size and len(raw) <= MAX_MANIFEST_BYTES,
            'manifest expanded size mismatch')
    require(hashlib.sha256(raw).hexdigest() == expected_sha, 'manifest SHA256 mismatch')
    value = strict_json(raw)
    require(isinstance(value, dict), 'manifest must be a JSON object')
    return value


def manifest_rows(rows):
    require(isinstance(rows, list) and len(rows) <= MAX_MEMBERS, 'invalid manifest list')
    result = {}
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'},
                'unexpected manifest row schema')
        name = safe_name(row['path'])
        require(name not in result, 'duplicate manifest path')
        require(type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_EXPANDED_BYTES,
                'invalid manifest byte count')
        require(valid_sha(row['sha256']), 'invalid manifest SHA256')
        result[name] = {'bytes': row['bytes'], 'sha256': row['sha256']}
    check_path_set(result)
    return result


def zip_inventory(archive):
    infos = archive.infolist()
    require(0 < len(infos) <= MAX_MEMBERS, 'ZIP member count outside limit')
    check_path_set([info.orig_filename for info in infos])
    result = {}
    total = 0
    for info in infos:
        require(info.orig_filename == info.filename, 'ZIP filename was truncated or changed')
        require(not info.is_dir(), 'explicit directory entries are not in this archive contract')
        require(not info.flag_bits & 1, 'encrypted ZIP member is unsupported')
        require(info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED),
                'unsupported ZIP compression')
        mode = (info.external_attr >> 16) & 0xFFFF
        require(stat.S_IFMT(mode) in (0, stat.S_IFREG) and not (info.external_attr & 0x10),
                'symlink, directory, or special ZIP member')
        require(type(info.file_size) is int and info.file_size >= 0, 'invalid ZIP file size')
        total += info.file_size
        require(total <= MAX_EXPANDED_BYTES, 'ZIP expanded byte limit exceeded')
        result[info.filename] = info
    return result, total


def expected_members(archive, infos):
    inner_name = 'candidate/MANIFEST.json'
    outer_name = 'PUBLICATION_MANIFEST.json'
    require(inner_name in infos and outer_name in infos, 'required manifests are absent')
    require(infos[inner_name].file_size == CANDIDATE_MANIFEST_BYTES,
            'candidate manifest byte count mismatch')
    inner = load_manifest(archive, infos[inner_name], CANDIDATE_MANIFEST_SHA256)
    require(type(inner.get('schema')) is int and inner['schema'] == 1,
            'unexpected candidate manifest schema')
    require(inner.get('self_hash_excluded') is True, 'candidate self-hash convention mismatch')
    entries = manifest_rows(inner.get('files'))
    require(len(entries) == CANDIDATE_LISTED_FILES and 'MANIFEST.json' not in entries,
            'candidate listed count or self-entry mismatch')
    candidate_payload_bytes = sum(row['bytes'] for row in entries.values())
    require(type(inner.get('content_bytes')) is int
            and inner['content_bytes'] == candidate_payload_bytes
            and candidate_payload_bytes + CANDIDATE_MANIFEST_BYTES == CANDIDATE_BYTES,
            'candidate content byte total mismatch')
    expected = {'candidate/' + name: row for name, row in entries.items()}
    expected[inner_name] = {'bytes': CANDIDATE_MANIFEST_BYTES,
                            'sha256': CANDIDATE_MANIFEST_SHA256}
    require(len(expected) == CANDIDATE_FILES, 'candidate full count mismatch')

    outer = load_manifest(archive, infos[outer_name], OUTER_MANIFEST_SHA256)
    require(outer.get('schema') == 'complete-six-public-review-v1', 'outer schema mismatch')
    require(outer.get('candidate_manifest_sha256') == CANDIDATE_MANIFEST_SHA256,
            'outer candidate manifest binding mismatch')
    require(type(outer.get('candidate_files')) is int and outer['candidate_files'] == CANDIDATE_FILES
            and type(outer.get('candidate_bytes')) is int and outer['candidate_bytes'] == CANDIDATE_BYTES,
            'outer candidate size/count binding mismatch')
    require(outer.get('self_hash_excluded') is True, 'outer self-hash convention mismatch')
    outer_rows = manifest_rows(outer.get('outer_files'))
    require({'README.md', 'SOURCE_NOTICE.md', 'REVIEWER_GUIDE.md', 'VERSION_MAP.json'} <= set(outer_rows),
            'required outer documents are absent')
    for name, row in outer_rows.items():
        require(name != outer_name and path_key(name.split('/')[0]) != 'candidate',
                'outer member conflicts with a reserved manifest or candidate namespace')
        require(name not in expected, 'outer/inner manifest collision')
        expected[name] = row
    expected[outer_name] = {'bytes': infos[outer_name].file_size, 'sha256': OUTER_MANIFEST_SHA256}
    check_path_set(expected)
    require(set(infos) == set(expected), 'ZIP member set does not exactly match both manifests')
    require(sum(row['bytes'] for row in expected.values()) <= MAX_EXPANDED_BYTES,
            'manifest expanded byte limit exceeded')
    for name, row in expected.items():
        require(infos[name].file_size == row['bytes'], 'ZIP header/manifest byte mismatch: ' + name)
    return expected, len(outer_rows)


def create_extract_root(value, state):
    # Resolve the existing parent, never silently create it or reuse an output.
    requested = Path(value)
    require(requested.name not in ('', '.', '..'), 'invalid extraction directory name')
    safe_name(requested.name)
    parent = requested.parent.resolve(strict=True)
    require(parent.is_dir(), 'extraction parent must already be a directory')
    target = parent / requested.name
    require(not os.path.lexists(target), 'extraction directory must not already exist')
    target.mkdir(mode=0o700)
    state['extraction_directory_created'] = True
    return target


def new_output_file(root, name):
    current = root
    # The inventory has already excluded symlinks, aliases and prefix conflicts.
    for part in PurePosixPath(name).parts[:-1]:
        current = current / part
        try:
            current.mkdir(mode=0o700)
        except FileExistsError:
            pass
        require(stat.S_ISDIR(current.lstat().st_mode), 'output parent is no longer an ordinary directory')
    require(root.resolve(strict=True) == root, 'extraction root was changed')
    require(current.resolve(strict=True).is_relative_to(root), 'output path escaped extraction root')
    return (current / PurePosixPath(name).name).open('xb')


def verify(args, state):
    require(valid_sha(ARCHIVE_SHA256) and valid_sha(OUTER_MANIFEST_SHA256)
            and type(ARCHIVE_BYTES) is int and ARCHIVE_BYTES > 0,
            'release-specific constants have not been configured')
    archive_path = Path(args.archive)
    with archive_path.open('rb') as raw:
        before = os.fstat(raw.fileno())
        require(stat.S_ISREG(before.st_mode), 'archive must be an ordinary file')
        require(before.st_size == ARCHIVE_BYTES, 'archive byte count mismatch')
        size, digest = stream_hash(raw, ARCHIVE_BYTES)
        require(size == ARCHIVE_BYTES and digest == ARCHIVE_SHA256, 'archive SHA256/size mismatch')
        state['archive_sha256_verified'] = True
        raw.seek(0)
        with zipfile.ZipFile(raw, 'r') as archive:
            infos, expanded_total = zip_inventory(archive)
            expected, outer_count = expected_members(archive, infos)
            root = create_extract_root(args.extract_to, state) if args.extract_to is not None else None
            verified_bytes = 0
            for name in sorted(expected):
                row = expected[name]
                output = new_output_file(root, name) if root is not None else None
                digest = hashlib.sha256()
                count = 0
                try:
                    with archive.open(infos[name], 'r') as source:
                        while True:
                            block = source.read(BLOCK_BYTES)
                            if not block:
                                break
                            count += len(block)
                            require(count <= row['bytes'], 'expanded member exceeds declared size')
                            digest.update(block)
                            if output is not None:
                                output.write(block)
                    require(count == row['bytes'] and digest.hexdigest() == row['sha256'],
                            'member SHA256/size mismatch: ' + name)
                finally:
                    if output is not None:
                        output.close()
                verified_bytes += count
                state['members_verified'] += 1
            require(verified_bytes == expanded_total, 'actual expanded total mismatch')
        after = os.fstat(raw.fileno())
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
                'archive metadata changed during verification')
    return {
        'status': 'PASS_DOWNLOAD_BYTES_AND_MEMBERS_ONLY',
        'archive_sha256': ARCHIVE_SHA256, 'archive_bytes': ARCHIVE_BYTES,
        'candidate_manifest_sha256': CANDIDATE_MANIFEST_SHA256,
        'publication_manifest_sha256': OUTER_MANIFEST_SHA256,
        'candidate_files': CANDIDATE_FILES, 'candidate_bytes': CANDIDATE_BYTES,
        'outer_listed_files': outer_count, 'archive_members': len(expected),
        'expanded_bytes_verified': verified_bytes,
        'extraction_completed': root is not None,
        'mathematical_verification_executed': False,
        'mathematical_acceptance_certified': False,
        'scope': 'Pinned archive and exact manifest-listed member bytes only.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, help='downloaded review ZIP')
    parser.add_argument('--extract-to', help='optional new directory; its parent must already exist')
    args = parser.parse_args()
    state = {'archive_sha256_verified': False, 'members_verified': 0,
             'extraction_directory_created': False}
    started = time.monotonic()
    try:
        result = verify(args, state)
        code = 0
    except (Exception, KeyboardInterrupt) as exc:
        result = {
            'status': 'REJECTED_DOWNLOAD_BYTES_OR_MEMBERS',
            'error_type': type(exc).__name__, 'error': str(exc),
            'progress': state,
            'partial_extraction_retained': state['extraction_directory_created'],
            'mathematical_verification_executed': False,
            'mathematical_acceptance_certified': False,
        }
        code = 1
    result['elapsed_seconds'] = round(time.monotonic() - started, 6)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True), flush=True)
    return code


if __name__ == '__main__':
    sys.exit(main())
