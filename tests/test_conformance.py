import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('conformance', ROOT / 'operations/conformance.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class RolloutConformance(unittest.TestCase):
    def setUp(self):
        self.doc = checker.load(ROOT / 'examples/network-rollout.json')

    def rejects(self, code):
        self.assertIn(code, {item['rule'] for item in checker.validate(self.doc)})

    def confirmed(self):
        for op in self.doc['operations']:
            target = next(t for t in self.doc['targets'] if t['id'] == op['target'])
            self.doc['receipts'].append({
                'operation': op['id'], 'target_identity': target['identity'], 'state': 'confirmed',
                'observed_config': op['desired_config'],
                'observed_firmware': op['firmware']['image_digest'] if op['firmware'] else op['expected_firmware'],
                'verification': 'pass', 'evidence_ref': 'fixture://readback/' + op['id'],
                'observer': 'fixture-observer', 'observed_at': '2026-09-24T12:00:00Z'})
        self.doc['state'] = 'confirmed'

    def test_network_plan(self):
        self.assertEqual([], checker.validate(self.doc))

    def test_firmware_plan(self):
        self.doc = checker.load(ROOT / 'examples/firmware-rollout.json')
        self.assertEqual([], checker.validate(self.doc))
        self.confirmed()
        self.assertEqual([], checker.validate(self.doc))

    def test_valid_confirmation(self):
        self.confirmed()
        self.assertEqual([], checker.validate(self.doc))

    def test_complete_rollback_is_representable(self):
        self.confirmed()
        self.doc['state'] = 'rolled_back'
        for receipt, op in zip(self.doc['receipts'], self.doc['operations']):
            receipt.update(state='rolled_back', observed_config=op['expected_config'],
                           observed_firmware=op['expected_firmware'])
        self.assertEqual([], checker.validate(self.doc))

    def test_query_cannot_change_configuration(self):
        self.doc['operations'][0].update(effect='query', apply='none',
                                        idempotency='not-applicable')
        self.rejects('OQL-010')

    def test_firmware_source_revision_length(self):
        self.doc = checker.load(ROOT / 'examples/firmware-rollout.json')
        self.doc['operations'][0]['firmware']['source_revision'] = 'a' * 41
        self.rejects('OQL-SCHEMA')

    def test_unknown_property(self):
        self.doc['trusted'] = True
        self.rejects('OQL-SCHEMA')

    def test_schema_version(self):
        self.doc['standard_version'] = '9.0.0'
        self.rejects('OQL-SCHEMA')

    def test_duplicate_setting_authority(self):
        self.doc['fields'].append(copy.deepcopy(self.doc['fields'][0]))
        self.rejects('OQL-002')

    def test_projection_cannot_write(self):
        source = copy.deepcopy(self.doc['sources'][0])
        source.update(id='mirror', role='projection', authority_source='system')
        self.doc['sources'].append(source)
        self.doc['precedence'].append('mirror')
        self.doc['operations'][0]['source'] = 'mirror'
        self.rejects('OQL-010')

    def test_unknown_target(self):
        self.doc['operations'][0]['target'] = 'typo'
        self.rejects('OQL-009')

    def test_no_target_substitution(self):
        self.confirmed()
        self.doc['receipts'][0]['target_identity'] = 'other-device'
        self.rejects('OQL-009')

    def test_missing_target_from_wave(self):
        self.doc['rollout']['waves'] = [['node-a']]
        self.rejects('OQL-019')

    def test_conflicting_revision(self):
        self.doc['operations'][0]['expected_config'] = 'f' * 64
        self.rejects('OQL-006')

    def test_mutation_requires_retry_policy(self):
        self.doc['operations'][0]['idempotency'] = 'not-applicable'
        self.rejects('OQL-012')

    def test_idempotency_header_alone_is_insufficient(self):
        self.doc['operations'][0]['idempotency'] = 'deduplicate'
        self.rejects('OQL-012')

    def test_trial_requires_rollback(self):
        self.doc['operations'][0]['rollback'] = None
        self.rejects('OQL-016')

    def test_firmware_requires_artifact_contract(self):
        self.doc['operations'][0].update(effect='firmware-update', apply='firmware')
        self.rejects('OQL-017')

    def test_compile_only_does_not_imply_provisioned_firmware(self):
        self.doc = checker.load(ROOT / 'examples/firmware-rollout.json')
        del self.doc['operations'][0]['firmware']['provisioning_ref']
        self.rejects('OQL-SCHEMA')

    def test_false_global_success(self):
        self.doc['state'] = 'confirmed'
        self.rejects('OQL-019')

    def test_wrong_image_readback(self):
        self.doc = checker.load(ROOT / 'examples/firmware-rollout.json')
        self.confirmed()
        self.doc['receipts'][0]['observed_firmware'] = 'f' * 64
        self.rejects('OQL-014')

    def test_http_acceptance_is_not_confirmation(self):
        self.confirmed()
        self.doc['receipts'][0].update(verification='not-run', evidence_ref=None)
        self.rejects('OQL-014')

    def test_unknown_outcome_blocks_later_wave(self):
        self.confirmed()
        self.doc['state'] = 'partial'
        self.doc['receipts'][0].update(state='outcome_unknown', verification='unknown')
        self.rejects('OQL-019')

    def test_partial_progress_is_representable(self):
        self.confirmed()
        self.doc['state'] = 'partial'
        self.doc['receipts'].pop()
        self.assertEqual([], checker.validate(self.doc))

    def test_twin_is_not_production_evidence(self):
        self.doc['targets'][0]['environment'] = 'real'
        self.rejects('OQL-024')

    def test_unsafe_include_path(self):
        self.doc['sources'][0]['path'] = '../../secrets'
        self.rejects('OQL-003')

    def test_documentary_setting_cannot_advertise_apply(self):
        self.doc['fields'][0]['support'] = 'documentary'
        self.rejects('OQL-005')

    def test_no_implicit_compiler_support(self):
        self.doc['dialect']['unknown_declarations'] = 'ignore'
        self.rejects('OQL-SCHEMA')

    def test_bad_timestamp(self):
        self.confirmed()
        self.doc['receipts'][0]['observed_at'] = 'sometime'
        self.rejects('OQL-SCHEMA')

    def test_json_duplicate_keys_and_nonfinite_rejected(self):
        # TemporaryDirectory is private test data, never a delivery checkout.
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'input.json'
            for raw in ('{"state":"planned","state":"confirmed"}', '{"value":NaN}', '{"value":Infinity}', '{"value":1e999}'):
                p.write_text(raw)
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    checker.load(p)

    def test_examples_are_explicit_fixtures(self):
        for path in (ROOT / 'examples').glob('*.json'):
            doc = checker.load(path)
            self.assertTrue(doc['id'].startswith('fixture-'))
            self.assertTrue(all(t['environment'] == 'twin' for t in doc['targets']))
            self.assertEqual('planned', doc['state'])
            self.assertEqual([], doc['receipts'])


if __name__ == '__main__':
    unittest.main()
