import { viem } from "hardhat";

async function main() {
  const publicClient = await viem.getPublicClient();
  const walletClient = await viem.getWalletClient();

  console.log("Deploying with:", walletClient.account.address);

  // Deploy Verifier
  const verifier = await viem.deployContract("Verifier");
  console.log("Verifier deployed at:", verifier.address);

  // Deploy AccessControl(verifier)
  const access = await viem.deployContract("AccessControl", [verifier.address]);
  console.log("AccessControl deployed at:", access.address);

  console.log("\nPUT THIS INTO python/.env:");
  console.log(`ACCESS_CONTROL_ADDRESS=${access.address}`);

  const block = await publicClient.getBlockNumber();
  console.log("Current block:", block.toString());
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
