"""Offline, hash-constrained reconstruction of two explicitly supplied files.

Usage: python restore_valueeval_local.py ORGANIZER_RAW ARCHIVE_RAW NEW_OUTPUT_DIR
No fetching or scientific execution occurs. A reconstructed HTML file is a
derived artifact, not a claim that its bytes were returned by a new HTTP request.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import re
import shutil
import sys

ORGANIZER_SIZE = 83506
ORGANIZER_SHA = 'f048152d2579be4d8fefa4c807221831233455de935d4ecb1b57f4a96e651fc8'
ARCHIVE_SIZE = 410492
ARCHIVE_SHA = '57c14d4055b28c52f0e644a5ff8a965a06c624d1a8987b79fe6b2be5074616ea'
FROZEN_TOKEN = b'1790154639'
ANCHOR = rb'    <link rel="stylesheet" href="/css/style\.css\?([0-9]{10})">\n    \n</head>\n'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bounded_read(path, size):
    require(path.is_file(), 'Input is not a file: ' + str(path))
    with path.open('rb') as handle:
        data = handle.read(size + 1)
    require(len(data) == size, 'Unexpected input size: ' + str(path))
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('organizer_raw', type=Path)
    parser.add_argument('archive_raw', type=Path)
    parser.add_argument('new_output_directory', type=Path)
    args = parser.parse_args()
    organizer_path = args.organizer_raw.resolve(strict=True)
    archive_path = args.archive_raw.resolve(strict=True)
    output = args.new_output_directory.absolute()
    require(organizer_path != archive_path, 'Two different input files are required.')
    require(output.parent.is_dir(), 'Output parent must already exist.')
    require(not output.exists() and not output.is_symlink(), 'Output must be a new directory.')
    require(shutil.disk_usage(output.parent).free >= 2 * 1024**2, 'Insufficient output space.')
    organizer = bounded_read(organizer_path, ORGANIZER_SIZE)
    archive = bounded_read(archive_path, ARCHIVE_SIZE)
    require(sha(archive) == ARCHIVE_SHA, 'Archive input must already match the frozen digest.')
    matches = list(re.finditer(ANCHOR, organizer))
    require(len(matches) == 1 and organizer.count(b'/css/style.css?') == 1,
            'Expected exactly one anchored CSS cache parameter.')
    token_start, token_end = matches[0].span(1)
    require((token_start, token_end) == (543, 553), 'Unexpected CSS parameter location.')
    incoming_token = organizer[token_start:token_end]
    restored = organizer[:token_start] + FROZEN_TOKEN + organizer[token_end:]
    require(len(restored) == ORGANIZER_SIZE and sha(restored) == ORGANIZER_SHA,
            'Restoration does not match the complete frozen organizer digest.')
    changed = [i for i, (before, after) in enumerate(zip(organizer, restored)) if before != after]
    require(all(token_start <= i < token_end for i in changed), 'Unexpected changed byte.')
    # All input and full-output checks precede creation. A failed write is retained.
    output.mkdir()
    rows = []
    for name, data in [('organizer_main.raw', restored), ('archive_evaluations.raw', archive)]:
        target = output / name
        with target.open('xb') as handle:
            handle.write(data)
        require(bounded_read(target, len(data)) == data, 'Output readback mismatch.')
        rows.append({'name': name, 'bytes': len(data), 'sha256': sha(data)})
    require(bounded_read(organizer_path, ORGANIZER_SIZE) == organizer, 'Organizer input changed.')
    require(bounded_read(archive_path, ARCHIVE_SIZE) == archive, 'Archive input changed.')
    receipt = {
        'schema': 1, 'status': 'PASS_EXACT_LOCAL_RESTORATION',
        'finished_utc': datetime.now(timezone.utc).isoformat(),
        'script_sha256': sha(Path(__file__).read_bytes()),
        'inputs': [
            {'path': str(organizer_path), 'bytes': len(organizer), 'sha256': sha(organizer)},
            {'path': str(archive_path), 'bytes': len(archive), 'sha256': sha(archive)}],
        'outputs': rows, 'output_directory': str(output),
        'transformation': {
            'kind': 'explicit_offline_CSS_cache_parameter_restoration',
            'zero_based_span_end_exclusive': [token_start, token_end],
            'incoming_token': incoming_token.decode('ascii'),
            'frozen_token': FROZEN_TOKEN.decode('ascii'),
            'changed_byte_offsets': changed,
            'archive_transformation': 'none'},
        'inputs_unchanged': True, 'network_access': False,
        'scientific_execution': False, 'historical_HTTP_authentication': False,
        'scope': 'Derived local bytes match an earlier frozen package. Acquisition provenance is separate; this does not prove historical execution or a new historical HTTP response.'}
    with (output / 'RESTORATION_RECEIPT_V01.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(json.dumps({'status': 'FAIL_LOCAL_RESTORATION', 'error': str(error),
                          'network_access': False, 'scientific_execution': False}), file=sys.stderr)
        sys.exit(1)
