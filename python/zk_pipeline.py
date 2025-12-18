import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CIRCUIT = ROOT / "circuits" / "age18.circom"
OUTDIR = ROOT / "artifacts_out"
OUTDIR.mkdir(exist_ok=True)

PTAU_0 = OUTDIR / "pot12_0000.ptau"
PTAU_FINAL = OUTDIR / "pot12_final.ptau"
PTAU_PHASE2 = OUTDIR / "pot12_final_phase2.ptau"

SNARKJS_CMD = r"C:\Users\visal\AppData\Roaming\npm\snarkjs.cmd"  # confirmed working in your logs

def run(cmd):
    print(" ".join(cmd))
    subprocess.run(["cmd", "/c"] + cmd, check=True)

def compile_circuit():
    run([
        "circom",
        str(CIRCUIT),
        "--r1cs", "--wasm", "--sym",
        "-l", str(ROOT / "node_modules"),
        "-o", str(OUTDIR)
    ])

def make_ptau_if_missing():
    # Create pot12_0000.ptau and pot12_final.ptau
    if not PTAU_FINAL.exists():
        run([SNARKJS_CMD, "powersoftau", "new", "bn128", "12", str(PTAU_0), "-v"])
        run([SNARKJS_CMD, "powersoftau", "contribute", str(PTAU_0), str(PTAU_FINAL)])
        # will prompt for entropy (you already handled it)

    # Prepare phase2 (required by groth16 setup)
    if not PTAU_PHASE2.exists():
        run([SNARKJS_CMD, "powersoftau", "prepare", "phase2", str(PTAU_FINAL), str(PTAU_PHASE2)])

def groth16_setup():
    make_ptau_if_missing()

    r1cs = OUTDIR / "age18.r1cs"
    zkey0 = OUTDIR / "age18_0000.zkey"
    zkey_final = OUTDIR / "age18_final.zkey"
    vkey = OUTDIR / "verification_key.json"
    verifier_sol = OUTDIR / "Verifier.sol"

    # Use phase2 ptau here
    run([SNARKJS_CMD, "groth16", "setup", str(r1cs), str(PTAU_PHASE2), str(zkey0)])

    # snarkjs 0.7.5: no --name/-v/-e (it will prompt for entropy)
    run([SNARKJS_CMD, "zkey", "contribute", str(zkey0), str(zkey_final)])

    run([SNARKJS_CMD, "zkey", "export", "verificationkey", str(zkey_final), str(vkey)])
    run([SNARKJS_CMD, "zkey", "export", "solidityverifier", str(zkey_final), str(verifier_sol)])

    print(f"\n✅ Verifier.sol generated at:\n{verifier_sol}")

def generate_proof(birth_year: int, current_year: int):
    wasm = OUTDIR / "age18_js" / "age18.wasm"
    input_json = OUTDIR / "input.json"
    witness = OUTDIR / "witness.wtns"
    proof_json = OUTDIR / "proof.json"
    public_json = OUTDIR / "public.json"
    zkey_final = OUTDIR / "age18_final.zkey"
    vkey = OUTDIR / "verification_key.json"

    input_json.write_text(json.dumps({
        "birthYear": birth_year,
        "currentYear": current_year
    }), encoding="utf-8")

    run([SNARKJS_CMD, "wtns", "calculate", str(wasm), str(input_json), str(witness)])
    run([SNARKJS_CMD, "groth16", "prove", str(zkey_final), str(witness), str(proof_json), str(public_json)])
    run([SNARKJS_CMD, "groth16", "verify", str(vkey), str(public_json), str(proof_json)])

    print("✅ Proof generated successfully")
    print(f" - proof.json  → {proof_json}")
    print(f" - public.json → {public_json}")

if __name__ == "__main__":
    compile_circuit()
    groth16_setup()
    generate_proof(birth_year=2002, current_year=2025)
