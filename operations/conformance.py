#!/usr/bin/env python3
"""Read-only validation of declared OQL rollout review records; never execute OQL."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path, PurePosixPath
import re

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 2 * 1024 * 1024
FORMATS = FormatChecker()


@FORMATS.checks('date-time', raises=(ValueError, TypeError))
def date_time(value):
    # jsonschema's optional format extras must not turn timestamps into a
    # silent pass when absent in the verifier's Python environment.
    if not isinstance(value, str) or not re.fullmatch(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', value
    ):
        return False
    return datetime.fromisoformat(value.replace('Z', '+00:00')).tzinfo is not None


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('document exceeds 2 MiB')
    def invalid_constant(value):
        raise ValueError(f'non-finite JSON number: {value}')
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            invalid_constant(value)
        return number
    return json.loads(raw, object_pairs_hook=_unique, parse_constant=invalid_constant, parse_float=finite_float)


def validate(document):
    schema = load(ROOT / 'schemas/rollout-review.schema.json')
    errors = sorted(Draft202012Validator(schema, format_checker=FORMATS).iter_errors(document),
                    key=lambda e: str(list(e.path)))
    findings = [{'rule': 'OQL-SCHEMA', 'path': '/'.join(map(str, e.path)), 'message': e.message}
                for e in errors]
    if findings:
        return findings

    def fail(rule, message):
        findings.append({'rule': rule, 'message': message})

    def index(rows, key, kind):
        result = {}
        for row in rows:
            if row[key] in result:
                fail('OQL-002', f'duplicate {kind}: {row[key]}')
            result[row[key]] = row
        return result

    sources = index(document['sources'], 'id', 'source')
    targets = index(document['targets'], 'id', 'target')
    operations = index(document['operations'], 'id', 'operation')
    if set(document['precedence']) != set(sources):
        fail('OQL-003', 'precedence must list every declared source exactly once')
    if len({t['identity'] for t in targets.values()}) != len(targets):
        fail('OQL-009', 'target identities must be distinct')
    for source in sources.values():
        path = PurePosixPath(source['path'])
        if path.is_absolute() or '..' in path.parts or '\\' in source['path'] or ':' in source['path']:
            fail('OQL-003', f'unsafe source path: {source["id"]}')
        authority = source['authority_source']
        if source['role'] == 'authority':
            if authority is not None:
                fail('OQL-002', 'authority cannot delegate ownership to another source')
        elif authority not in sources or sources[authority]['role'] != 'authority':
            fail('OQL-002', 'seed, projection and observation must reference a declared authority')

    index(document['fields'], 'key', 'setting owner')
    for field in document['fields']:
        source = sources.get(field['source'])
        if not source:
            fail('OQL-005', f'unknown setting source: {field["key"]}')
        if field['support'] == 'writable':
            if not source or source['role'] != 'authority':
                fail('OQL-002', 'writable setting requires an authoritative source')
            if field['apply'] == 'none' or not field['write_operation'] or not field['verification']:
                fail('OQL-005', 'writable setting requires apply mode, writer and verification')
            if field['apply'] in ('restart-trial', 'firmware') and not field['rollback']:
                fail('OQL-016', 'disruptive setting requires a recovery method')
        elif field['write_operation'] is not None or field['apply'] != 'none':
            fail('OQL-005', 'non-writable settings cannot advertise a runtime apply operation')

    wave_targets = [item for wave in document['rollout']['waves'] for item in wave]
    if len(wave_targets) != len(set(wave_targets)) or set(wave_targets) != set(targets):
        fail('OQL-019', 'waves must cover the exact target set once')
    if len({t['environment'] for t in targets.values()}) > 1:
        fail('OQL-024', 'this review profile requires separate real and twin rollouts')
    for operation in operations.values():
        target = targets.get(operation['target'])
        source = sources.get(operation['source'])
        if not target or not source:
            fail('OQL-009', 'operation refers to an undeclared target or source')
            continue
        if not target['compatible']:
            fail('OQL-017', 'incompatible targets must not enter an executable rollout')
        if operation['expected_config'] != target['current_config'] or operation['expected_firmware'] != target['current_firmware']:
            fail('OQL-006', 'operation precondition differs from the observed target revision')
        if operation['desired_config'] != target['desired_config']:
            fail('OQL-014', 'operation must bind the target desired configuration')
        if operation['effect'] in ('query', 'actuate') and operation['desired_config'] != operation['expected_config']:
            fail('OQL-010', 'query and actuation must preserve the configuration revision')
        if operation['effect'] == 'query':
            if operation['apply'] != 'none' or operation['firmware'] is not None or operation['idempotency'] != 'not-applicable':
                fail('OQL-010', 'query must not claim a configuration or firmware effect')
        else:
            if source['role'] != 'authority' or not operation['capability'] or not operation['readback']:
                fail('OQL-010', 'mutation requires authority, capability and readback')
            if operation['idempotency'] == 'not-applicable':
                fail('OQL-012', 'mutation requires an explicit retry/reconciliation policy')
            if operation['idempotency'] == 'deduplicate' and operation['deduplication_window_s'] <= 0:
                fail('OQL-012', 'deduplication requires a positive retention window')
            if operation['apply'] == 'none':
                fail('OQL-010', 'mutation must declare its apply mode')
        if operation['apply'] == 'restart-trial' and not operation['rollback']:
            fail('OQL-016', 'trial activation requires rollback')
        is_firmware = operation['effect'] == 'firmware-update'
        if is_firmware != (operation['firmware'] is not None) or is_firmware != (operation['apply'] == 'firmware'):
            fail('OQL-017', 'firmware effects require the complete firmware contract and apply mode')
        if is_firmware and not operation['rollback']:
            fail('OQL-018', 'firmware update requires rollback/recovery')
    # One operation per target keeps this first profile unambiguous. Dependent
    # operations on the same target use separate plans with fresh preconditions.
    if len({o['target'] for o in operations.values()}) != len(operations) or {o['target'] for o in operations.values()} != set(targets):
        fail('OQL-019', 'profile v1 requires exactly one operation for each target')

    receipts = index(document['receipts'], 'operation', 'receipt')
    for op_id, receipt in receipts.items():
        operation = operations.get(op_id)
        if not operation or operation['target'] not in targets:
            fail('OQL-014', 'receipt has no declared operation/target')
            continue
        target = targets[operation['target']]
        if receipt['target_identity'] != target['identity']:
            fail('OQL-009', 'receipt identity does not match the target')
        state = receipt['state']
        if state in ('confirmed', 'rolled_back'):
            firmware = operation['firmware']
            expected_fw = firmware['image_digest'] if firmware and state == 'confirmed' else operation['expected_firmware']
            expected_config = operation['desired_config'] if state == 'confirmed' else operation['expected_config']
            if receipt['verification'] != 'pass' or not receipt['evidence_ref']:
                fail('OQL-014', 'confirmation/rollback requires declared successful verification evidence')
            if receipt['observed_config'] != expected_config or receipt['observed_firmware'] != expected_fw:
                fail('OQL-014', 'readback revision/image differs from the declared final state')
        elif receipt['verification'] == 'pass':
            fail('OQL-013', 'non-terminal state cannot claim completed verification')

    state = document['state']
    observed_states = [r['state'] for r in receipts.values()]
    if state in ('confirmed', 'rolled_back') and (set(receipts) != set(operations) or any(s != state for s in observed_states)):
        fail('OQL-019', 'global terminal success requires a matching receipt for every operation')
    if state == 'planned' and any(s not in ('desired', 'validated', 'staged') for s in observed_states):
        fail('OQL-013', 'planned cannot hide observed execution effects')
    if state == 'outcome_unknown' and 'outcome_unknown' not in observed_states:
        fail('OQL-013', 'unknown aggregate requires an unknown operation receipt')
    if state == 'failed' and 'failed' not in observed_states:
        fail('OQL-013', 'failed aggregate requires a failed operation receipt')
    if state == 'partial' and (not receipts or (len(receipts) == len(operations) and len(set(observed_states)) == 1 and observed_states[0] in ('confirmed', 'rolled_back'))):
        fail('OQL-019', 'partial requires observed incomplete or mixed progress')
    prior = []
    by_target = {o['target']: o for o in operations.values()}
    for wave in document['rollout']['waves']:
        advanced = any(receipts.get(by_target.get(t, {}).get('id'), {}).get('state') in
                       ('applying', 'trial', 'confirmed', 'failed', 'outcome_unknown') for t in wave)
        if advanced and any(receipts.get(by_target.get(t, {}).get('id'), {}).get('state') != 'confirmed' for t in prior):
            # Recovery receipts describe restored state, not forward advancement.
            # Mixed recovery/forward histories require separate review plans.
            fail('OQL-019', 'later wave advanced without confirmed prior-wave receipts')
        prior.extend(wave)
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('document', type=Path)
    args = parser.parse_args(argv)
    try:
        findings = validate(load(args.document))
    except (ValueError, OSError, UnicodeError, RecursionError) as error:
        findings = [{'rule': 'OQL-INPUT', 'message': str(error)}]
    print(json.dumps({'schema': 'wellmanifest.oql/conformance/v1', 'valid': not findings,
                      'coverage': 'declared-schema-and-cross-field-consistency-only',
                      'authority': 'none', 'device_effects': False,
                      'unverified': ['OQL syntax and compiler', 'identity/provenance authenticity',
                                     'authorization enforcement', 'live state', 'test execution'],
                      'findings': findings}, indent=2))
    return int(bool(findings))


if __name__ == '__main__':
    raise SystemExit(main())
