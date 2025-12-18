import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CIRCUIT = ROOT / "circuits" / "age18.circom"
OUTDIR = ROOT / "artifacts_out"
OUTDIR.mkdir(exist_ok=True)

PTAU = OUTDIR / "powersOfTau28_hez_final_10.ptau"  # you must download once

def run(cmd: list[str], cwd: Path | None = None):
    print(" ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)

def ensure_ptau():
    if PTAU.exists():
        return
    raise FileNotFoundError(
        f"Missing {PTAU.name}. Download a powersOfTau ptau file and place it at: {PTAU}"
    )

def compile_circuit():
    # circom age18.circom --r1cs --wasm --sym
    run(["circom", str(CIRCUIT), "--r1cs", "--wasm", "--sym", "-o", str(OUTDIR)])

def groth16_setup():
    ensure_ptau()

    r1cs = OUTDIR / "age18.r1cs"
    zkey0 = OUTDIR / "age18_0000.zkey"
    zkey_final = OUTDIR / "age18_final.zkey"
    vkey = OUTDIR / "verification_key.json"
    verifier_sol = OUTDIR / "Verifier.sol"

    # snarkjs groth16 setup age18.r1cs ptau age18_0000.zkey
    run(["snarkjs", "groth16", "setup", str(r1cs), str(PTAU), str(zkey0)])

    # contribute (for demo you can do a single contribution)
    run(["snarkjs", "zkey", "contribute", str(zkey0), str(zkey_final),
         "--name", "first", "-v", "-e", "some random entropy"])

    # export verification key
    run(["snarkjs", "zkey", "export", "verificationkey", str(zkey_final), str(vkey)])

    # export solidity verifier contract :contentReference[oaicite:5]{index=5}
    run(["snarkjs", "zkey", "export", "solidityverifier", str(zkey_final), str(verifier_sol)])

    print("Generated verifier:", verifier_sol)

def generate_proof(birth_year: int, current_year: int):
    """
    Generates proof.json + public.json
    Public signal: currentYear
    Private: birthYear
    """
    wasm_dir = OUTDIR / "age18_js"
    wasm = wasm_dir / "age18.wasm"
    input_json = OUTDIR / "input.json"
    witness_wtns = OUTDIR / "witness.wtns"
    proof_json = OUTDIR / "proof.json"
    public_json = OUTDIR / "public.json"
    zkey_final = OUTDIR / "age18_final.zkey"

    # write input
    input_data = {
        "birthYear": birth_year,
        "currentYear": current_year
    }
    input_json.write_text(json.dumps(input_data), encoding="utf-8")

    # witness generation using snarkjs (no custom JS needed)
    # snarkjs wtns calculate age18.wasm input.json witness.wtns
    run(["snarkjs", "wtns", "calculate", str(wasm), str(input_json), str(witness_wtns)])

    # proof
    # snarkjs groth16 prove final.zkey witness.wtns proof.json public.json
    run(["snarkjs", "groth16", "prove", str(zkey_final), str(witness_wtns), str(proof_json), str(public_json)])

    # optional local verify
    vkey = OUTDIR / "verification_key.json"
    run(["snarkjs", "groth16", "verify", str(vkey), str(public_json), str(proof_json)])

    print("proof:", proof_json)
    print("public:", public_json)

if __name__ == "__main__":
    compile_circuit()
    groth16_setup()
    # demo example: born 2000, currentYear 2025 => adult
    generate_proof(birth_year=2000, current_year=2025)
