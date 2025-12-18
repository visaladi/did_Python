import json
import os
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

load_dotenv(Path(__file__).parent / ".env")

RPC_URL = os.getenv("RPC_URL")
CHAIN_ID = int(os.getenv("CHAIN_ID", "80001"))
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
ACCESS_CONTROL_ADDRESS = os.getenv("ACCESS_CONTROL_ADDRESS")

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "artifacts_out"
PROOF_PATH = OUTDIR / "proof.json"
PUBLIC_PATH = OUTDIR / "public.json"

# Minimal ABI for AccessControl.verifyAgeOver18
ACCESS_ABI = [
    {
        "inputs": [
            {"internalType": "uint256[2]", "name": "a", "type": "uint256[2]"},
            {"internalType": "uint256[2][2]", "name": "b", "type": "uint256[2][2]"},
            {"internalType": "uint256[2]", "name": "c", "type": "uint256[2]"},
            {"internalType": "uint256[1]", "name": "publicSignals", "type": "uint256[1]"},
        ],
        "name": "verifyAgeOver18",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    }
]

def _to_int(x: str) -> int:
    # snarkjs outputs decimal strings
    return int(x)

def load_snarkjs_proof():
    proof = json.loads(PROOF_PATH.read_text(encoding="utf-8"))
    public = json.loads(PUBLIC_PATH.read_text(encoding="utf-8"))

    # snarkjs groth16 proof format:
    # proof.pi_a = [Ax, Ay, 1]
    # proof.pi_b = [[Bx1, Bx0], [By1, By0], [1,0]]
    # proof.pi_c = [Cx, Cy, 1]
    # Many Solidity verifiers expect:
    # a = [Ax, Ay]
    # b = [[Bx0, Bx1], [By0, By1]]  (note swap order)
    # c = [Cx, Cy]
    pi_a = proof["pi_a"]
    pi_b = proof["pi_b"]
    pi_c = proof["pi_c"]

    a = [_to_int(pi_a[0]), _to_int(pi_a[1])]
    # swap inner order for bn128 pairing precompile convention used by snarkjs verifier
    b = [
        [_to_int(pi_b[0][1]), _to_int(pi_b[0][0])],
        [_to_int(pi_b[1][1]), _to_int(pi_b[1][0])]
    ]
    c = [_to_int(pi_c[0]), _to_int(pi_c[1])]
    publicSignals = [_to_int(public[0])]  # currentYear

    return a, b, c, publicSignals

def verify_on_chain():
    if not RPC_URL or not ACCESS_CONTROL_ADDRESS:
        raise RuntimeError("Set RPC_URL and ACCESS_CONTROL_ADDRESS in python/.env")

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError("RPC not reachable. Change RPC_URL.")

    contract = w3.eth.contract(address=Web3.to_checksum_address(ACCESS_CONTROL_ADDRESS), abi=ACCESS_ABI)
    a, b, c, publicSignals = load_snarkjs_proof()

    # View call (no gas needed)
    ok = contract.functions.verifyAgeOver18(a, b, c, publicSignals).call()
    print("On-chain verify:", ok)
    return ok

if __name__ == "__main__":
    verify_on_chain()
