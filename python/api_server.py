import subprocess
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

from chain_verify import verify_on_chain
from zk_pipeline import generate_proof

app = FastAPI(title="DID + ZK Access Control (Python)")

class ProveReq(BaseModel):
    birthYear: int
    currentYear: int

class VerifyResp(BaseModel):
    ok: bool

@app.post("/prove")
def prove(req: ProveReq):
    # Generate proof.json/public.json into artifacts_out
    generate_proof(req.birthYear, req.currentYear)
    return {"status": "proof_generated"}

@app.get("/verify", response_model=VerifyResp)
def verify():
    ok = verify_on_chain()
    return VerifyResp(ok=ok)
