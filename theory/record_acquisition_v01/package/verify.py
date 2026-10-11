"""Portable standard-library verification of a fixed record-acquisition source."""
import argparse
from datetime import datetime, timezone
import functools
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

SOURCE_SHA = '87734e80539d8f60a26477c3acf8a760cdafa35f3cb4a27f78802be564d0b62e'
POLICY_SHA = 'ffad6d25138cc63f614bc3d1556b3f20853abdcbf20581004fd8db11c18ff795'
FILES = {'source.json', 'budget15_policy.json', 'verify.py', 'README.md'}
MAX_STATES = 300000
MAX_SECONDS = 120
MAX_INPUT_BYTES = 1024 * 1024
MAX_RESULT_BYTES = 256 * 1024
PASS = 'PASS_RECORD_ACQUISITION_VERIFICATION'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def object_unique(pairs):
    answer = {}
    for key, value in pairs:
        require(key not in answer, 'duplicate JSON key')
        answer[key] = value
    return answer


def reject_constant(value):
    raise ValueError('nonfinite JSON constant')


def json_read(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=object_unique,
                      parse_constant=reject_constant)


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def inventory(bundle):
    """Validate the entire flat package and return relative bindings and data."""
    require(bundle.is_dir(), 'bundle is not a directory')
    entries = list(bundle.iterdir())
    require({p.name for p in entries} == FILES | {'MANIFEST.json'}, 'unexpected package inventory')
    require(all(p.is_file() and not p.is_symlink() for p in entries), 'nonregular package entry')
    require(sum(p.stat().st_size for p in entries) <= MAX_INPUT_BYTES, 'package input cap')
    data = {p.name: p.read_bytes() for p in entries}
    manifest = json_read(data['MANIFEST.json'])
    require(manifest.get('schema') == 'RECORD_ACQUISITION_PACKAGE_MANIFEST_V01', 'wrong manifest schema')
    rows = manifest.get('files')
    require(isinstance(rows, list) and len(rows) == len(FILES), 'wrong manifest entry count')
    require(all(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'} for row in rows), 'bad manifest row')
    require({row['path'] for row in rows} == FILES, 'wrong or duplicate manifest path')
    for row in rows:
        require(type(row['bytes']) is int and row['bytes'] == len(data[row['path']]), 'manifest size mismatch')
        require(row['sha256'] == sha(data[row['path']]), 'manifest SHA mismatch')
    require(sha(data['source.json']) == SOURCE_SHA, 'wrong frozen source bytes')
    require(sha(data['budget15_policy.json']) == POLICY_SHA, 'wrong original policy bytes')
    bindings = [{'path': name, 'bytes': len(raw), 'sha256': sha(raw)} for name, raw in sorted(data.items())]
    return bindings, data


class DSU:
    def __init__(self, count):
        self.parent = list(range(count))

    def find(self, record):
        while record != self.parent[record]:
            record = self.parent[record]
        return record

    def join(self, a, b):
        self.parent[self.find(b)] = self.find(a)


class Verification:
    def __init__(self, source, started):
        self.source = source
        self.started = started
        require(source['record_ids'] == list(range(14)), 'wrong record set')
        require(source['matched_prices'] == {'integer_weights': [4, 4, 4, 4, 6, 6, 1, 1, 2, 2, 2, 2, 2, 2], 'denominator': 4}, 'wrong matched prices')
        require(source['unit_control'] == {'integer_weights': [1] * 14, 'denominator': 1}, 'wrong unit prices')
        self.priors = {label: (source[label + '_same_blocks'], source[label + '_different']) for label in ('A', 'B')}
        for same, negative in self.priors.values():
            require(sorted(x for block in same for x in block) == list(range(14)), 'prior SAME blocks not partition')
            require(all(len(pair) == 2 and all(type(x) is int and 0 <= x < 14 for x in pair) for pair in negative), 'bad prior negative pair')
        self.weights = tuple(source['matched_prices']['integer_weights'])
        for name in ('matched_priority_order', 'unit_priority_order'):
            require(sorted(source[name]) == list(range(14)), 'order is not permutation')
        self.states = 0

    def checkpoint(self):
        if time.perf_counter() - self.started > MAX_SECONDS:
            raise TimeoutError('cooperative 120-second verification cap')

    def completion(self, label, records, answers):
        """Exact extendability of a partial observed partition, using constraints.

        If equality closure violates no prior or observed inequality, distinct
        DSU components supply a full legal partition. This uses complete fibres.
        """
        self.checkpoint()
        require(len(records) == len(set(records)) == len(answers), 'invalid partial history')
        dsu = DSU(14)
        same, negative = self.priors[label]
        for block in same:
            for record in block[1:]:
                dsu.join(block[0], record)
        unequal = list(map(tuple, negative))
        for i, x in enumerate(records):
            for j in range(i):
                y = records[j]
                if answers[i] == answers[j]:
                    dsu.join(x, y)
                else:
                    unequal.append((x, y))
        if any(dsu.find(x) == dsu.find(y) for x, y in unequal):
            return None
        names, world = {}, []
        for record in range(14):
            representative = dsu.find(record)
            if representative not in names:
                names[representative] = len(names)
            world.append(names[representative])
        require(all(len({world[x] for x in block}) == 1 for block in same), 'wrong constructed SAME completion')
        require(all(world[x] != world[y] for x, y in negative), 'wrong constructed DIFFERENT completion')
        require(all((world[x] == world[y]) == (answers[i] == answers[j])
                    for i, x in enumerate(records) for j, y in enumerate(records)), 'wrong constructed projection')
        return world

    def unit_control(self):
        pairs = third_cases = checks = 0
        witness_digest = hashlib.sha256()
        left, right = {0, 4, 8}, {1, 5, 9}
        for pair in itertools.combinations(range(14), 2):
            unequal = ((4 in pair and any(x in right for x in pair if x != 4)) or
                       (5 in pair and any(x in left for x in pair if x != 5)))
            first = [0, 1] if unequal else [0, 0]
            require(all(self.completion(label, pair, first) is not None for label in self.priors), 'first pair not mixed')
            pairs += 1
            for third in range(14):
                if third in pair:
                    continue
                selected = None
                for response in range(max(first) + 2):
                    checks += 1
                    observed = first + [response]
                    records = list(pair) + [third]
                    worlds = {label: self.completion(label, records, observed) for label in self.priors}
                    if all(world is not None for world in worlds.values()):
                        selected = {'records': records, 'answers': observed, 'completions': worlds}
                        break
                require(selected is not None, 'a third acquisition eliminates all common projections')
                witness_digest.update(compact(selected) + b'\n')
                third_cases += 1
        require(pairs == 91 and third_cases == 1092, 'incomplete unit lower bound')
        ranks = {record: i for i, record in enumerate(self.source['unit_priority_order'])}
        leaves, visits = [], 0

        def visit(records, answers):
            nonlocal visits
            visits += 1
            labels = {label: self.completion(label, records, answers) is not None for label in self.priors}
            require(any(labels.values()), 'unreachable upper-bound state')
            if len(records) < 2:
                record = len(records)
            else:
                branch = [4, 5] if answers[0] == answers[1] else [2, 3]
                if len(records) == 4:
                    label = 'A' if answers[2] == answers[3] else 'B'
                    require(labels[label] and not labels['B' if label == 'A' else 'A'], 'unit leaf not pure/correct')
                    require(all(ranks[x] < ranks[y] for x, y in zip(records, records[1:])), 'unit order violation')
                    leaves.append({'records': records, 'answers': answers, 'label': label})
                    return
                record = branch[len(records) - 2]
            for response in range(max(answers, default=-1) + 2):
                after_r, after_a = records + [record], answers + [response]
                if any(self.completion(label, after_r, after_a) is not None for label in self.priors):
                    visit(after_r, after_a)

        visit([], [])
        require(leaves and max(len(leaf['records']) for leaf in leaves) == 4, 'no unit four-read upper bound')
        return {'first_pairs': pairs, 'third_cases': third_cases, 'candidate_response_checks': checks,
                'all_third_choices_have_both_label_completions': True,
                'constructed_witness_stream_sha256': witness_digest.hexdigest(),
                'upper_reachable_states': visits, 'upper_terminal_states': len(leaves),
                'upper_leaf_stream_sha256': sha(compact(leaves)),
                'upper_max_cost': 4, 'all_upper_leaves_correct_and_ordered': True,
                'adaptive': 4, 'strong_priority': 4,
                'lower_argument': 'The first read has no information. Each first unordered pair has a fixed mixed answer, and every possible third record retains both labels. Thus some path needs at least four reads.'}

    @staticmethod
    def canonical(state):
        names, answer = {}, []
        for value in state:
            if value == -1:
                answer.append(-1)
            else:
                if value not in names:
                    names[value] = len(names)
                answer.append(names[value])
        return tuple(answer)

    def weighted_check(self, policy):
        @functools.lru_cache(maxsize=MAX_STATES)
        def live(state):
            self.checkpoint()
            records = [record for record in range(14) if state[record] != -1]
            values = [state[record] for record in records]
            return tuple(self.completion(label, records, values) is not None for label in ('A', 'B'))

        def children(state, record):
            result = []
            for response in range(max(state) + 2):
                changed = list(state)
                changed[record] = response
                child = self.canonical(changed)
                if any(live(child)):
                    result.append((response, child))
            return result

        def spent(state):
            return sum(self.weights[r] for r in range(14) if state[r] != -1)

        @functools.lru_cache(maxsize=None)
        def feasible14(state):
            self.states += 1
            require(self.states <= MAX_STATES, 'budget recurrence state cap; incomplete')
            self.checkpoint()
            labels = live(state)
            require(any(labels), 'unreachable feasibility state')
            if sum(labels) == 1:
                return True
            remaining = 14 - spent(state)
            for record in range(14):
                if state[record] != -1 or self.weights[record] > remaining:
                    continue
                next_states = children(state, record)
                require(next_states, 'no feasible next response')
                if all(feasible14(child) for _, child in next_states):
                    return True
            return False

        empty = (-1,) * 14
        feasible = feasible14(empty)
        require(feasible is False, 'budget14 unexpectedly feasible')
        ranks = {record: i for i, record in enumerate(self.source['matched_priority_order'])}
        leaves, node_count = [], 0

        def inspect(node, state, trace):
            nonlocal node_count
            self.checkpoint()
            node_count += 1
            require(isinstance(node, dict), 'policy node is not object')
            labels = live(state)
            require(any(labels), 'policy branch unreachable')
            if set(node) == {'label'}:
                label = node['label']
                require(label in ('A', 'B'), 'invalid terminal label')
                require(labels == ((True, False) if label == 'A' else (False, True)), 'terminal not pure/correct')
                value = spent(state)
                require(value <= 15, 'saved policy exceeds budget15')
                require(all(ranks[a] < ranks[b] for a, b in zip(trace, trace[1:])), 'path order violation')
                leaves.append({'records': trace, 'partition': list(state), 'label': label, 'cost': value})
                return
            require(set(node) == {'record', 'branches'}, 'invalid policy node shape')
            record = node['record']
            require(type(record) is int and 0 <= record < 14 and state[record] == -1, 'invalid/repeated acquisition')
            require(not trace or ranks[record] > ranks[trace[-1]], 'backward priority edge')
            require(isinstance(node['branches'], list), 'branches not list')
            actual = {}
            for branch in node['branches']:
                require(isinstance(branch, dict) and set(branch) == {'matches_record', 'next'}, 'invalid response shape')
                match = branch['matches_record']
                require(type(match) is int, 'response representative not integer')
                if match == -1:
                    response = max(state) + 1
                else:
                    require(0 <= match < 14 and state[match] != -1, 'response refers to unread record')
                    response = state[match]
                require(response not in actual, 'duplicate equality-class response')
                actual[response] = branch['next']
            expected = dict(children(state, record))
            require(set(actual) == set(expected), 'missing or infeasible response branch')
            for response, child in expected.items():
                inspect(actual[response], child, trace + [record])

        inspect(policy, empty, [])
        require(leaves and max(leaf['cost'] for leaf in leaves) == 15, 'saved maximum cost is not15')
        return {'budget14_feasible': feasible, 'budget14_states': self.states,
                'budget14_cache': feasible14.cache_info()._asdict(),
                'liveness_cache': live.cache_info()._asdict(),
                'policy_nodes': node_count, 'policy_terminal_states': len(leaves),
                'policy_leaf_stream_sha256': sha(compact(leaves)), 'policy_max_integer_cost': 15,
                'all_feasible_policy_branches_covered': True, 'all_terminals_pure_and_correct': True,
                'all_paths_increase_in_global_order': True,
                'fixed_order': self.source['matched_priority_order'],
                'denominator': 4, 'adaptive': '15/4', 'strong_priority': '15/4',
                'lower_argument': 'The recurrence allows every affordable unacquired record and all DSU-feasible responses. With integer acquisition costs, infeasible budget14 implies minimum cost at least15.',
                'priority_argument': 'The next purchased record depends only on purchased answers. Increasing paths in one global order allow causal permanent skips without revealing skipped answers.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    output = args.output.resolve()
    require(not output.is_relative_to(bundle), 'output must be outside bundle')
    require(not output.exists(), 'refuse output overwrite')
    started = time.perf_counter()
    result = {'schema': 'RECORD_ACQUISITION_VERIFICATION_V01', 'status': 'INCOMPLETE_OR_FAILED',
              'human_review': False, 'python_version': sys.version.split()[0],
              'caps': {'cooperative_seconds': MAX_SECONDS, 'feasibility_states': MAX_STATES},
              'full_world_enumeration': False, 'producer_or_repository_imports': False,
              'all_order_enumeration': False, 'network_used': False,
              'scope': 'Portable replay of the existing finite synthetic record-acquisition result. No natural-data, historical-provenance, practical-benefit or novelty claim.'}
    try:
        require(sys.version_info >= (3, 10), 'Python3.10 or later required')
        before, payload = inventory(bundle)
        result['inputs'] = before
        require(sha(Path(__file__).read_bytes()) == sha(payload['verify.py']), 'running verifier differs from package verifier')
        source = json_read(payload['source.json'])
        require(source.get('schema') == 'COMPLETE_SOURCE_RECORD_ACQUISITION_V01', 'wrong source schema')
        verification = Verification(source, started)
        result['unit_control'] = verification.unit_control()
        result['matched_prices'] = verification.weighted_check(json_read(payload['budget15_policy.json']))
        verification.checkpoint()
        after, _ = inventory(bundle)
        require(before == after, 'package changed during verification')
        result['inputs_unchanged'] = True
        result['status'] = PASS
    except Exception as exc:
        result['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    result['elapsed_seconds_before_output'] = time.perf_counter() - started
    result['completed_at_utc'] = datetime.now(timezone.utc).isoformat()
    encoded = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    require(len(encoded) <= MAX_RESULT_BYTES, 'result size cap')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as handle:
        handle.write(encoded)
    print(json.dumps({'status': result['status'], 'result_bytes': len(encoded),
                      'result_sha256': sha(encoded),
                      'unit': {'adaptive': result.get('unit_control', {}).get('adaptive'), 'strong_priority': result.get('unit_control', {}).get('strong_priority')},
                      'matched': {'adaptive': result.get('matched_prices', {}).get('adaptive'), 'strong_priority': result.get('matched_prices', {}).get('strong_priority')},
                      'elapsed_seconds': time.perf_counter() - started}))
    return 0 if result['status'] == PASS else 2


if __name__ == '__main__':
    raise SystemExit(main())
