# Mapping Path

Locate and prove a raw word behind **nested Solidity mappings**, optionally
adding a final struct word offset. This helps a worker request the right
EIP-1186 slot for layouts such as nested allowance mappings or mapped structs.
Unlike the existing single address-key Balance Slot helper, this supports
multiple typed keys, signed integers and fixed bytes with their different
padding rules. Layout identification is still the caller's responsibility.

From the repository root, Python 3.9+ standard library only:

```sh
python3 -B line-2/tools/mapping-path/mapping_path.py demo
```

## What happened when tried

The offline demo derived the assigned **real ZTO/IMD Uniswap v4 pool** slot
from its bytes32 pool ID and mapping base slot 6. The resulting raw key was
`0x85763e16f60121d4266264cb693cca4d6bdb9e98ff9cc3d698d892d90342971b`.
The inherited execution header and account/storage witness verified against
the historical block hash at block **26,212,390**; the proven word was
`0x30d400000001b32f000000000000010675ff9d949ea2d3c11613bc41`.
The input layout follows the existing Pool State helper. No current pool
state, price, token balance or fresh RPC observation is claimed. The example
checkpoint is an inherited RPC observation, not independently authenticated.
Historical public source: <https://ethereum-rpc.publicnode.com>.

The focused tests cover the real proof, nested mapping order, struct offsets,
integer width/sign boundaries, left versus right padding, modulo slot
arithmetic, malformed/oversized paths, duplicate JSON fields, path pinning,
changed files, forged values, incomplete proofs and clean CLI failures.

```sh
python3 -B -m unittest discover -s line-2/tools/mapping-path -p 'test_*.py' -v
```

## Inputs and commands

Use the exact schema in `examples/zto-pool-path.json`:

| Field | Meaning |
| --- | --- |
| `format` | Exactly `mapping-path/1` |
| `address` | Actual 20-byte contract/account address |
| `baseSlot` | Canonical 0x-prefixed uint256 quantity naming the outer mapping's storage slot |
| `keys` | 1..8 objects, outermost first, each containing only `type` and `value` |
| `wordOffset` | Canonical unsigned decimal string, uint256, added after all mapping hashes |

Supported key types and values:

| Type | Value and encoding |
| --- | --- |
| `address` | Exact 20-byte hex string, left padded to 32 bytes |
| `bool` | JSON boolean, encoded as a 32-byte 0 or 1 |
| `uintN` | Canonical unsigned decimal string fitting N bits, left padded |
| `intN` | Canonical signed decimal string fitting N bits, sign extended to 32 bytes |
| `bytesN` | Exact N-byte hex string, **right padded** to 32 bytes |

Integer N must be a multiple of 8 from 8 through 256; bytes N is 1 through 32.
Use explicit widths (`uint256`, not `uint`). Signs on unsigned values, `-0`,
leading decimal zeros, JSON numbers and whitespace fail. Dynamic `bytes` and
`string` keys, enum/user-defined types, arrays, tuples and intermediate struct
offsets are unsupported and rejected. A final offset counts **whole words**,
not bytes or bit fields. No packed field extraction occurs.

For every key the tool computes Ethereum legacy Keccak-256 over
`encodedKey32 || currentSlot32`, then uses that hash as the next mapping's
slot. The final offset is added modulo 2^256 and `offsetWrapped` reports
wrapping. Every preimage and intermediate slot appears in the result.
This is not standardized SHA3-256 or packed ABI encoding.

Derive a candidate key without claiming proof validity:

```sh
python3 -B line-2/tools/mapping-path/mapping_path.py derive line-2/tools/mapping-path/examples/zto-pool-path.json
```

That prints `verified: false` and an exact-file `pathSha256`. After independently
reviewing and retaining your own path digest and block hash, use `verify`.
This explicit command reproduces the historical demo:

```sh
python3 -B line-2/tools/mapping-path/mapping_path.py verify \
  line-2/tools/mapping-path/examples/zto-pool-path.json \
  line-2/tools/header-anchor/examples/zto-header-mainnet.json \
  line-2/tools/state-witness/examples/zto-pool-mainnet.json \
  --block-hash 0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc \
  --path-sha256 0x62b8957f9faedfbdbbe9ca241cc184b06f0d8b16f622aa40cc4597e176071b19
```

For real use, replace the path, header, witness and both pins with your own
reviewed inputs. Copying a digest or checkpoint from the evidence provider
alone authenticates nothing. The witness must cover **exactly one slot**, the
derived final slot. A larger proof set is rejected. Bundle address/slot/block
labels cannot override the path or caller checkpoint. The account must exist;
proven absence of storage in that account is accepted as zero with
`storageExists: false`. Missing proof nodes are errors, not zero values.

Exit 0 prints the complete result. Exit 1 prints error JSON on stderr with no
partial success output. Argument errors exit 2. Derivation also exits 0, so
consumers requiring proof must demand `verified: true`. The exact-file path
SHA-256 is mandatory for `verify`; it is checked before proof loading, and the
path is reread before success. This detects ordinary changes during checking,
not an atomic filesystem snapshot; keep all inputs static.

Path files are bounded to 16 KiB; headers to 64 KiB; witnesses to the inherited
1 MB and proof-node limits. Unknown/missing path fields, duplicate JSON keys,
NaN and input paths/symlinks escaping the working directory fail. No runtime
networking, package installation, environment/configuration discovery, wallet,
secret, signing, sending, payment, posting, deployment or file writing occurs.
Keep sibling `header-anchor/` and `state-witness/` with this folder; the demo
uses their unchanged historical example files. There are no new dependencies.

A proof authenticates raw bytes relative to a supplied checkpoint. It cannot
prove that a chosen mapping declaration matches deployed code, identify a
proxy implementation, establish token semantics or predict behavior. The caller
must authenticate the checkpoint, chain, canonicality, execution validity and
finality independently. Nested derivation tests are arithmetic checks; only
the pool demonstration claims real historical state. No new coin is needed.
