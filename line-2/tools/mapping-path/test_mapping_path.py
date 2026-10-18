"""Real Ethereum integration plus adversarial static-key encoding checks."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch, MagicMock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('mapping_path_tests', HERE / 'mapping_path.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MappingPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path, cls.digest = m.load_path(HERE / 'examples/zto-pool-path.json')
        cls.header = m.a.load_header(HERE.parent / 'header-anchor/examples/zto-header-mainnet.json')
        cls.bundle = m.w.load_bundle(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json')

    def check(self, path=None, header=None, bundle=None, checkpoint=None):
        return m.verify(self.path if path is None else path,
                        self.header if header is None else header,
                        self.bundle if bundle is None else bundle,
                        m.a.DEMO_HASH if checkpoint is None else checkpoint)

    def key(self, kind, value):
        return m.encode_key({'type': kind, 'value': value})

    def test_real_pool_slot_and_value(self):
        result = self.check()
        self.assertTrue(result['verified'])
        self.assertEqual(result['storageSlot'], m.a.POOL_SLOT)
        self.assertEqual(int(result['anchor']['blockNumber'], 16), 26212390)
        self.assertTrue(result['storageExists'])
        self.assertEqual(result['rawWord'],
                         '0x30d400000001b32f000000000000010675ff9d949ea2d3c11613bc41')
        self.assertEqual(int(result['rawWordDecimal']), int(result['rawWord'], 16))

    def test_derivation_does_not_claim_proof(self):
        result = m.derive(self.path)
        self.assertFalse(result['verified'])
        self.assertNotIn('state', result)
        # Ethereum Keccak differs from standardized SHA3, including this real key.
        preimage = bytes.fromhex(result['steps'][0]['preimage'][2:])
        self.assertNotEqual(hashlib.sha3_256(preimage).hexdigest(), m.a.POOL_SLOT[2:])

    def test_address_uint_bool_padding(self):
        self.assertEqual(self.key('address', m.w.ZTO), b'\0' * 12 + bytes.fromhex(m.w.ZTO[2:]))
        self.assertEqual(self.key('uint8', '255'), b'\0' * 31 + b'\xff')
        self.assertEqual(self.key('uint256', str((1 << 256)-1)), b'\xff' * 32)
        self.assertEqual(self.key('bool', True), b'\0' * 31 + b'\x01')
        self.assertEqual(self.key('bool', False), b'\0' * 32)

    def test_bytesN_is_right_padded_not_integer_encoding(self):
        self.assertEqual(self.key('bytes2', '0x1234'), b'\x12\x34' + b'\0' * 30)
        self.assertNotEqual(self.key('bytes2', '0x1234'), self.key('uint16', '4660'))
        self.assertEqual(self.key('bytes32', m.w.ZTO_POOL_ID), bytes.fromhex(m.w.ZTO_POOL_ID[2:]))

    def test_signed_keys_sign_extend_and_enforce_width(self):
        for bits in (8, 16, 128, 256):
            self.assertEqual(self.key(f'int{bits}', '-1'), b'\xff' * 32)
            low = -(1 << (bits-1))
            self.assertEqual(int.from_bytes(self.key(f'int{bits}', str(low)), 'big', signed=True), low)
            for value in (str(low-1), str(-low)):
                with self.assertRaises(m.w.Invalid):
                    self.key(f'int{bits}', value)
        self.assertEqual(self.key('int8', '127'), b'\0' * 31 + b'\x7f')

    def test_nested_mapping_order_and_final_offset(self):
        path = copy.deepcopy(self.path)
        path.update(baseSlot='0x9', keys=[{'type': 'address', 'value': m.w.ZTO},
                                        {'type': 'address', 'value': m.w.POOL_MANAGER}],
                    wordOffset='2')
        first = m.w.keccak256(bytes.fromhex(m.w.ZTO[2:]).rjust(32, b'\0') + (9).to_bytes(32, 'big'))
        second = m.w.keccak256(bytes.fromhex(m.w.POOL_MANAGER[2:]).rjust(32, b'\0') + first)
        result = m.derive(path)
        self.assertEqual(result['steps'][1]['inputSlot'], hex(int.from_bytes(first, 'big')))
        self.assertEqual(result['storageSlot'], m.w.hex0((int.from_bytes(second, 'big')+2).to_bytes(32, 'big')))
        path['keys'].reverse()
        self.assertNotEqual(m.derive(path)['storageSlot'], result['storageSlot'])

    def test_offset_wrap_is_explicit_modulo_uint256(self):
        path = copy.deepcopy(self.path)
        root = int(m.a.POOL_SLOT, 16)
        path['wordOffset'] = str((1 << 256)-root+7)
        result = m.derive(path)
        self.assertTrue(result['offsetWrapped'])
        self.assertEqual(int(result['storageSlot'], 16), 7)

    def test_integer_types_values_and_widths_reject_ambiguity(self):
        bad = [('uint', '1'), ('int', '-1'), ('uint7', '1'), ('uint264', '1'),
               ('uint08', '1'), ('uint16', 1), ('uint8', True), ('uint8', '256'),
               ('uint8', '-1'), ('int8', '-0'), ('int8', '+1'), ('int8', '01'),
               ('int256', '9' * 80), ('bool', 1), ('bool', 'true')]
        for kind, value in bad:
            with self.subTest(kind=kind, value=value), self.assertRaises(m.w.Invalid):
                self.key(kind, value)

    def test_dynamic_and_malformed_keys_fail(self):
        for kind, value in [('string', 'ZTO'), ('bytes', '0x12'), ('bytes0', '0x'),
                            ('bytes33', '0x12'), ('bytes2', '0x12'), ('bytes1', '0x1234'),
                            ('address', m.w.ZTO + '00'), ('address', '0x1'),
                            ('bytes1', '0xGG'), ('bytes1', '0x1'), (None, '0')]:
            with self.subTest(kind=kind), self.assertRaises(m.w.Invalid):
                self.key(kind, value)
        with self.assertRaises(m.w.Invalid):
            m.encode_key({'type': 'uint8', 'value': '1', 'extra': True})

    def test_path_shape_and_resource_bounds(self):
        for name, value in [('format', 'other'), ('baseSlot', '0x06'), ('baseSlot', '-1'),
                            ('baseSlot', hex(1 << 256)), ('wordOffset', '-1'),
                            ('wordOffset', str(1 << 256)), ('wordOffset', '00'),
                            ('wordOffset', 0), ('keys', []), ('keys', {}),
                            ('keys', self.path['keys'] * 9)]:
            path = copy.deepcopy(self.path)
            path[name] = value
            with self.subTest(name=name, value=value), self.assertRaises(m.w.Invalid):
                m.derive(path)
        path = copy.deepcopy(self.path)
        path['keys'] *= 8
        self.assertEqual(len(m.derive(path)['steps']), 8)
        for path in (None, [], dict(self.path, extra=True)):
            with self.assertRaises(m.w.Invalid):
                m.derive(path)

    def test_wrong_checkpoint_header_address_path_fail(self):
        with self.assertRaises(m.w.Invalid):
            self.check(checkpoint='0x' + 'ab' * 32)
        header = copy.deepcopy(self.header)
        header['stateRoot'] = '0x' + 'ab' * 32
        with self.assertRaises(m.w.Invalid):
            self.check(header=header)
        for key, value in [('address', m.w.ZTO), ('baseSlot', '0x7'), ('wordOffset', '1')]:
            path = copy.deepcopy(self.path)
            path[key] = value
            with self.subTest(key=key), self.assertRaises(m.w.Invalid):
                self.check(path=path)

    def test_forged_value_and_missing_proof_fail(self):
        for target in ('value', 'nodes', 'extra'):
            bundle = copy.deepcopy(self.bundle)
            row = bundle['proof']['storageProof'][0]
            if target == 'value':
                row['value'] = '0x0'
            elif target == 'nodes':
                row['proof'] = []
            else:
                bundle['proof']['storageProof'].append(copy.deepcopy(row))
            with self.subTest(target=target), self.assertRaises(m.w.Invalid):
                self.check(bundle=bundle)

    def test_bundle_metadata_does_not_select_layout_or_checkpoint(self):
        bundle = copy.deepcopy(self.bundle)
        bundle.update(address=m.w.ZTO, slots=['0x0'], chainId=999, block={})
        self.assertEqual(self.check(bundle=bundle), self.check())

    def test_inputs_remain_unchanged(self):
        before = copy.deepcopy((self.path, self.header, self.bundle))
        self.check()
        self.assertEqual(before, (self.path, self.header, self.bundle))

    def test_real_absent_word_is_zero_not_a_missing_proof(self):
        # Deliberately contrived offset lands at raw slot 0; this tests proof
        # handling, not a claim that ZTO has this invented mapping layout.
        path = copy.deepcopy(self.path)
        path['address'] = m.w.ZTO
        path['wordOffset'] = str((-int(m.a.POOL_SLOT, 16)) % (1 << 256))
        bundle = m.w.load_bundle(HERE.parent / 'state-witness/examples/zto-mainnet.json')
        bundle['proof']['storageProof'] = [bundle['proof']['storageProof'][0]]
        result = self.check(path=path, bundle=bundle)
        self.assertFalse(result['storageExists'])
        self.assertEqual(result['rawWordDecimal'], '0')
        self.assertTrue(result['state']['accountExists'])
        bundle['proof']['storageProof'][0]['proof'] = []
        with self.assertRaises(m.w.Invalid):
            self.check(path=path, bundle=bundle)

    def test_nonexistent_account_is_rejected_even_with_valid_absence(self):
        # Synthetic empty-root header/proof isolates this boundary; never used
        # as a demo checkpoint or represented as real chain data.
        header = copy.deepcopy(self.header)
        header.pop('hash')
        header['stateRoot'] = m.w.hex0(m.w.EMPTY_TRIE)
        checkpoint = m.w.hex0(m.w.keccak256(m.a.encode_header(header)[0]))
        slot = m.derive(self.path)['storageSlot']
        bundle = {'format': 'state-witness/1', 'proof': {
            'address': self.path['address'], 'nonce': '0x0', 'balance': '0x0',
            'storageHash': m.w.hex0(m.w.EMPTY_TRIE), 'codeHash': m.w.hex0(m.w.EMPTY_CODE),
            'accountProof': [], 'storageProof': [{'key': slot, 'value': '0x0', 'proof': []}]}}
        with self.assertRaisesRegex(m.w.Invalid, 'existing account'):
            self.check(header=header, bundle=bundle, checkpoint=checkpoint)

    def test_json_limits_duplicates_and_workspace_boundary(self):
        with self.assertRaises(m.w.Invalid):
            m.load_path(Path.cwd().parent / 'not-in-workspace.json')
        for raw in (b'{"keys": [], "keys": []}', b'{"keys": NaN}', b' ' * (m.MAX_PATH+1)):
            virtual_path = MagicMock()
            virtual_path.open.return_value = io.BytesIO(raw)
            with patch.object(m.w, 'workspace_path', return_value=virtual_path):
                with self.assertRaises(m.w.Invalid):
                    m.load_path('in-memory')

    def test_cli_pin_and_no_partial_success(self):
        argv = ['verify', str(HERE / 'examples/zto-pool-path.json'),
                str(HERE.parent / 'header-anchor/examples/zto-header-mainnet.json'),
                str(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json'),
                '--block-hash', m.a.DEMO_HASH, '--path-sha256', '0x' + self.digest]
        with patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(m.main(argv), 0)
            self.assertTrue(json.loads(out.getvalue())['verified'])
        for index, bad in [(-1, '0x' + 'ab' * 32), (-3, '0x' + 'ab' * 32)]:
            changed = argv[:]
            changed[index] = bad
            with patch('sys.stdout', new_callable=io.StringIO) as out, \
                    patch('sys.stderr', new_callable=io.StringIO) as err:
                self.assertEqual(m.main(changed), 1)
                self.assertEqual(out.getvalue(), '')
                self.assertFalse(json.loads(err.getvalue())['verified'])

    def test_changed_path_during_check_is_rejected(self):
        with patch.object(m, 'load_path', side_effect=[(self.path, self.digest),
                                                      (self.path, 'ab' * 32)]), \
                patch('sys.stdout', new_callable=io.StringIO) as out, \
                patch('sys.stderr', new_callable=io.StringIO) as err:
            self.assertEqual(m.main(['demo']), 1)
            self.assertEqual(out.getvalue(), '')
            self.assertIn('changed during', json.loads(err.getvalue())['error'])

    def test_command_line_entrypoint(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'mapping_path.py'), 'demo'],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['verified'])
        result = subprocess.run([sys.executable, '-B', str(HERE / 'mapping_path.py'), 'verify'],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
