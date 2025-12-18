import json
import requests
from pathlib import Path

IPFS_API = "http://127.0.0.1:5001/api/v0/add"

def ipfs_add_json(data: dict) -> str:
    tmp = Path("credential_metadata.json")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")

    with open(tmp, "rb") as f:
        r = requests.post(IPFS_API, files={"file": f})
    r.raise_for_status()
    cid = r.json()["Hash"]
    return cid

if __name__ == "__main__":
    metadata = {
        "claim": "AGE_OVER_18",
        "issuer": "DemoIssuer",
        "issued_at": 1700000000
    }
    cid = ipfs_add_json(metadata)
    print("IPFS CID:", cid)
