from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from python.chain_verify import verify_on_chain
from python.zk_pipeline import generate_proof

app = FastAPI(title="Local Hardhat ZK Access Control (Python)")

# Serve UI
app.mount("/ui", StaticFiles(directory="python/ui", html=True), name="ui")

@app.get("/")
def root():
    return FileResponse("python/ui/index.html")

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
