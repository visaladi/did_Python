from fastapi import FastAPI
from pydantic import BaseModel
from zk_pipeline import generate_proof
from chain_verify import verify_on_chain

app = FastAPI(title="Local Hardhat ZK Access Control (Python)")

class ProveReq(BaseModel):
    birthYear: int
    currentYear: int

@app.post("/prove")
def prove(req: ProveReq):
    generate_proof(req.birthYear, req.currentYear)
    return {"status": "proof_generated"}

@app.get("/verify")
def verify():
    return {"ok": verify_on_chain()}
