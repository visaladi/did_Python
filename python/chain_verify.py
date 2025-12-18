import json
import os
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

load_dotenv(Path(__file__).parent / ".env")

RPC_URL = os.getenv("RPC_URL")
CHAIN_ID = int(os.getenv("CHAIN_ID", "31337"))
ACCESS_CONTROL_ADDRESS = os.getenv("ACCESS_CONTROL_ADDRESS")

# Minimal ABI for AccessControl.verifyAgeOver18(...)
ACCESS_ABI = [
    {
        "inputs": [
            {"internalType": "uint256[2]", "name": "a", "type": "uint256[2]"},
            {"internalType": "uint256[2][2]", "name": "b", "type": "uint256[2][2]"},
            {"internalType": "uint256[2]", "name": "c", "type": "uint256[2]"},
            {"internalType": "uint256[2]", "name": "publicSignals", "type": "uint256[2]"},
        ],
        "name": "verifyAgeOver18",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    }
]

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "artifacts_out"

def load_snarkjs_proof():
    proof = json.loads((OUTDIR / "proof.json").read_text(encoding="utf-8"))
    public = json.loads((OUTDIR / "public.json").read_text(encoding="utf-8"))

    # snarkjs outputs strings; convert to int
    a = [int(proof["pi_a"][0]), int(proof["pi_a"][1])]
    # IMPORTANT: swap order inside b for Solidity verifier compatibility
    b = [
        [int(proof["pi_b"][0][1]), int(proof["pi_b"][0][0])],
        [int(proof["pi_b"][1][1]), int(proof["pi_b"][1][0])],
    ]
    c = [int(proof["pi_c"][0]), int(proof["pi_c"][1])]
    publicSignals = [int(public[0]), int(public[1])]


    return a, b, c, publicSignals

def verify_on_chain() -> bool:
    if not RPC_URL:
        raise RuntimeError("RPC_URL missing in python/.env")
    if not ACCESS_CONTROL_ADDRESS:
        raise RuntimeError("ACCESS_CONTROL_ADDRESS missing in python/.env (deploy first)")

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError("Cannot connect to local Hardhat RPC (is `npx hardhat node` running?)")

    # optional sanity check
    if w3.eth.chain_id != CHAIN_ID:
        raise RuntimeError(f"ChainId mismatch. Expected {CHAIN_ID}, got {w3.eth.chain_id}")

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(ACCESS_CONTROL_ADDRESS),
        abi=ACCESS_ABI
    )

    a, b, c, publicSignals = load_snarkjs_proof()
    ok = contract.functions.verifyAgeOver18(a, b, c, publicSignals).call()
    print("On-chain verification:", ok)
    return bool(ok)

if __name__ == "__main__":
    verify_on_chain()
