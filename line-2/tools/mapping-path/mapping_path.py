#!/usr/bin/env python3
"""Derive a typed Solidity mapping path and verify its final raw storage word.

Offline standard-library only. Inputs are caller-reviewed layout assumptions,
never layout discovery. No network, environment access or file writes.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'mapping_path_anchor', HERE.parent / 'header-anchor' / 'anchor.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
w = a.w
UINT256 = 1 << 256
MAX_PATH = 16_384


def exact_keys(value, keys):
    w.require(isinstance(value, dict) and set(value) == set(keys),
              'missing or unknown path/key field')


def decimal(value, signed=False):
    pattern = r'(?:0|-?[1-9][0-9]*)' if signed else r'(?:0|[1-9][0-9]*)'
    w.require(isinstance(value, str) and len(value) <= 79 and
              re.fullmatch(pattern, value) is not None,
              'integer values must be canonical decimal strings')
    return int(value)


def encode_key(key):
    """Solidity h(k) for supported static value types, exactly 32 bytes.

    bytesN is right padded; address/uint/bool left padded; int sign extended.
    Dynamic bytes/string keys, arrays, tuples and user-defined types are refused.
    """
    exact_keys(key, ('type', 'value'))
    kind, value = key['type'], key['value']
    w.require(isinstance(kind, str), 'mapping key type must be a string')
    if kind == 'address':
        return w.hex_data(value, 20, 'address key').rjust(32, b'\0')
    if kind == 'bool':
        w.require(type(value) is bool, 'bool key must be a JSON boolean')
        return int(value).to_bytes(32, 'big')
    match = re.fullmatch(r'(uint|int)([1-9][0-9]{0,2})', kind)
    if match:
        signed, bits = match[1] == 'int', int(match[2])
        w.require(8 <= bits <= 256 and bits % 8 == 0,
                  'integer key width must be 8..256 in steps of 8')
        number = decimal(value, signed)
        low, high = (-(1 << (bits-1)), 1 << (bits-1)) if signed else (0, 1 << bits)
        w.require(low <= number < high, 'mapping key is outside its declared integer width')
        return (number % UINT256).to_bytes(32, 'big')
    match = re.fullmatch(r'bytes([1-9]|[12][0-9]|3[0-2])', kind)
    if match:
        return w.hex_data(value, int(match[1]), 'bytesN key').ljust(32, b'\0')
    raise w.Invalid('unsupported mapping key type; use address, bool, uintN, intN or bytesN')


def derive(path):
    exact_keys(path, ('format', 'address', 'baseSlot', 'keys', 'wordOffset'))
    w.require(path['format'] == 'mapping-path/1', 'unsupported path format')
    address = w.hex0(w.hex_data(path['address'], 20, 'contract address'))
    slot = w.quantity(path['baseSlot'], 'base slot')
    offset = decimal(path['wordOffset'])
    w.require(offset < UINT256, 'word offset exceeds uint256')
    keys = path['keys']
    w.require(isinstance(keys, list) and 1 <= len(keys) <= 8,
              'path requires 1..8 mapping keys, outermost first')
    steps = []
    for key in keys:
        word = encode_key(key)
        preimage = word + slot.to_bytes(32, 'big')
        hashed = w.keccak256(preimage)
        steps.append({'type': key['type'], 'keyWord': w.hex0(word),
                      'inputSlot': hex(slot), 'preimage': w.hex0(preimage),
                      'mappingSlot': w.hex0(hashed)})
        slot = int.from_bytes(hashed, 'big')
    return {
        'format': 'mapping-path-result/1', 'verified': False,
        'address': address, 'baseSlot': hex(w.quantity(path['baseSlot'])),
        'steps': steps, 'wordOffset': str(offset),
        'offsetWrapped': slot + offset >= UINT256,
        'storageSlot': w.hex0(((slot + offset) % UINT256).to_bytes(32, 'big')),
        'assumption': ('Caller must confirm the contract layout, mapping base, key types/order '
                       'and final struct word offset. Derivation alone proves no state or layout.'),
    }


def load_path(path):
    with w.workspace_path(path).open('rb') as stream:
        raw = stream.read(MAX_PATH + 1)
    w.require(len(raw) <= MAX_PATH, 'path exceeds 16 KiB limit')
    return w.parse_json(raw), hashlib.sha256(raw).hexdigest()


def verify(path, header, bundle, block_hash):
    result = derive(path)
    proof = a.verify(header, bundle, block_hash, result['address'], [result['storageSlot']])
    # A missing account is distinguishable from a present account's zero word.
    # Do not attach an interpretation to unallocated contract storage.
    w.require(proof['state']['accountExists'], 'mapping verification requires an existing account')
    row = proof['state']['storage'][0]
    result.update({'verified': True, 'anchor': proof['anchor'], 'state': proof['state'],
                   'storageExists': row['exists'], 'rawWord': row['value'],
                   'rawWordDecimal': str(int(row['value'], 16)),
                   'trust': ('Only the raw word at the derived slot is proven relative to the '
                             'supplied block hash. Authenticate checkpoint, chain, canonicality '
                             'and finality independently; storage layout and token meaning remain '
                             'caller assumptions. No current-state or behavior claim is made.')})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='offline real historical ZTO/IMD mapped pool word')
    derive_cli = sub.add_parser('derive', help='derive a candidate raw slot without proving it')
    derive_cli.add_argument('path')
    check = sub.add_parser('verify', help='verify one mapped word at a trusted block hash')
    check.add_argument('path')
    check.add_argument('header')
    check.add_argument('witness')
    check.add_argument('--block-hash', required=True)
    check.add_argument('--path-sha256', required=True,
                       help='separately retained exact-file path digest (32-byte 0x hex)')
    args = parser.parse_args(argv)
    try:
        path_file = HERE / 'examples/zto-pool-path.json' if args.command == 'demo' else args.path
        path, digest = load_path(path_file)
        if args.command == 'derive':
            result = derive(path)
        else:
            if args.command == 'demo':
                header_file = HERE.parent / 'header-anchor/examples/zto-header-mainnet.json'
                witness_file = HERE.parent / 'state-witness/examples/zto-pool-mainnet.json'
                block_hash = a.DEMO_HASH
            else:
                w.require(w.hex_data(args.path_sha256, 32, 'path SHA-256') == bytes.fromhex(digest),
                          'path SHA-256 differs from expected')
                header_file, witness_file, block_hash = args.header, args.witness, args.block_hash
            result = verify(path, a.load_header(header_file), w.load_bundle(witness_file), block_hash)
            # Reject a changed path even if replacement happened during proof checking.
            w.require(load_path(path_file)[1] == digest, 'path changed during verification')
            if args.command == 'demo':
                result['demo'] = ('Historical real ZTO/IMD proof, no fresh RPC. Fixed hash is an '
                                  'RPC observation, not an independently authenticated checkpoint.')
        result['pathSha256'] = digest
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except w.Invalid as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print(json.dumps({'verified': False, 'error': 'Unreadable or malformed path, header or witness.'}),
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
