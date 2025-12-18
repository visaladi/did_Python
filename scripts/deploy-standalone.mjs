import { ethers } from "ethers";
import fs from "fs";
import path from "path";

const RPC_URL = "http://127.0.0.1:8545";
const PRIVATE_KEY = process.env.DEPLOYER_PRIVATE_KEY;

if (!PRIVATE_KEY) {
  console.error("Missing DEPLOYER_PRIVATE_KEY env var");
  process.exit(1);
}

function artifact(fileName, contractName) {
  const p = path.join(
    process.cwd(),
    "artifacts",
    "contracts",
    `${fileName}.sol`,
    `${contractName}.json`
  );
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

async function main() {
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);

  console.log("Deploying with:", wallet.address);

  // IMPORTANT: file name is Verifier.sol, contract name is Groth16Verifier
  const VerifierArt = artifact("Verifier", "Groth16Verifier");
  const AccessArt = artifact("AccessControl", "AccessControl");

  // Deploy Groth16Verifier
  const VerifierFactory = new ethers.ContractFactory(
    VerifierArt.abi,
    VerifierArt.bytecode,
    wallet
  );
  const verifier = await VerifierFactory.deploy();
  await verifier.waitForDeployment();
  const verifierAddr = await verifier.getAddress();
  console.log("Groth16Verifier deployed at:", verifierAddr);

  // Deploy AccessControl(verifierAddr)
  const AccessFactory = new ethers.ContractFactory(
    AccessArt.abi,
    AccessArt.bytecode,
    wallet
  );
  const access = await AccessFactory.deploy(verifierAddr);
  await access.waitForDeployment();
  const accessAddr = await access.getAddress();
  console.log("AccessControl deployed at:", accessAddr);

  console.log("\nPUT THIS INTO python/.env:");
  console.log(`ACCESS_CONTROL_ADDRESS=${accessAddr}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
