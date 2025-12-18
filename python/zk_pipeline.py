import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CIRCUIT = ROOT / "circuits" / "age18.circom"
OUTDIR = ROOT / "artifacts_out"
OUTDIR.mkdir(exist_ok=True)

# For LOCAL Hardhat demo, we can generate a small ptau ourselves (no download needed).
PTAU = OUTDIR / "pot12_final.ptau"

def run(cmd: list[str]):
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

def compile_circuit():
    # circom age18.circom --r1cs --wasm --sym -o artifacts_out
    run(["circom", str(CIRCUIT), "--r1cs", "--wasm", "--sym", "-o", str(OUTDIR)])

def make_ptau_if_missing():
    if PTAU.exists():
        return

    # Small ceremony for demo (fast). Security-grade ceremonies use larger powers.
    # 12 is adequate for small circuits.
    pot0 = OUTDIR / "pot12_0000.ptau"

    run(["snarkjs", "powersoftau", "new", "bn128", "12", str(pot0), "-v"])
    run(["snarkjs", "powersoftau", "contribute", str(pot0), str(PTAU),
         "--name", "local-demo", "-v", "-e", "random entropy"])

def groth16_setup():
    make_ptau_if_missing()

    r1cs = OUTDIR / "age18.r1cs"
    zkey0 = OUTDIR / "age18_0000.zkey"
    zkey_final = OUTDIR / "age18_final.zkey"
    vkey = OUTDIR / "verification_key.json"
    verifier_sol = OUTDIR / "Verifier.sol"

    run(["snarkjs", "groth16", "setup", str(r1cs), str(PTAU), str(zkey0)])
    run(["snarkjs", "zkey", "contribute", str(zkey0), str(zkey_final),
         "--name", "local-demo-2", "-v", "-e", "more entropy"])

    run(["snarkjs", "zkey", "export", "verificationkey", str(zkey_final), str(vkey)])
    run(["snarkjs", "zkey", "export", "solidityverifier", str(zkey_final), str(verifier_sol)])

    print(f"[OK] Generated Verifier.sol at: {verifier_sol}")
    print("Copy this file into your Hardhat contracts folder as contracts/Verifier.sol")

def generate_proof(birth_year: int, current_year: int):
    wasm_dir = OUTDIR / "age18_js"
    wasm = wasm_dir / "age18.wasm"
    input_json = OUTDIR / "input.json"
    witness_wtns = OUTDIR / "witness.wtns"
    proof_json = OUTDIR / "proof.json"
    public_json = OUTDIR / "public.json"
    zkey_final = OUTDIR / "age18_final.zkey"
    vkey = OUTDIR / "verification_key.json"

    input_data = {"birthYear": birth_year, "currentYear": current_year}
    input_json.write_text(json.dumps(input_data), encoding="utf-8")

    run(["snarkjs", "wtns", "calculate", str(wasm), str(input_json), str(witness_wtns)])
    run(["snarkjs", "groth16", "prove", str(zkey_final), str(witness_wtns), str(proof_json), str(public_json)])
    run(["snarkjs", "groth16", "verify", str(vkey), str(public_json), str(proof_json)])

    print(f"[OK] proof.json:  {proof_json}")
    print(f"[OK] public.json: {public_json}")

if __name__ == "__main__":
    compile_circuit()
    groth16_setup()
    # Example demo proof
    generate_proof(birth_year=2002, current_year=2025)
