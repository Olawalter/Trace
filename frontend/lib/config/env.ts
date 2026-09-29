/**
 * What this console needs to know before it can do anything, checked once.
 *
 * There is no server and no fallback: if the address or the chain is missing,
 * the app says which variable is wrong rather than quietly reading somebody
 * else's contract.
 */

export type AppConfig = {
  network: string;
  chainId: number;
  contractAddress: `0x${string}`;
  explorer: string;
  rpc: string;
};

export type ConfigResult =
  | { ok: true; config: AppConfig }
  | { ok: false; problems: { name: string; found: string; wanted: string }[] };

const NETWORKS: Record<string, { chainId: number; rpc: string; explorer: string }> = {
  studionet: {
    chainId: 61999,
    rpc: "https://studio.genlayer.com/api",
    explorer: "https://explorer-studio.genlayer.com",
  },
};

function read(): ConfigResult {
  const problems: { name: string; found: string; wanted: string }[] = [];
  const network = (process.env.NEXT_PUBLIC_GENLAYER_NETWORK ?? "").trim().toLowerCase();
  const chain = (process.env.NEXT_PUBLIC_CHAIN_ID ?? "").trim();
  const address = (process.env.NEXT_PUBLIC_TRACE_CONTRACT_ADDRESS ?? "").trim();

  const known = NETWORKS[network];
  if (!known) {
    problems.push({
      name: "NEXT_PUBLIC_GENLAYER_NETWORK",
      found: network || "(not set)",
      wanted: `one of ${Object.keys(NETWORKS).join(", ")}`,
    });
  }
  const chainId = Number(chain);
  if (!chain || Number.isNaN(chainId) || (known && chainId !== known.chainId)) {
    problems.push({
      name: "NEXT_PUBLIC_CHAIN_ID",
      found: chain || "(not set)",
      wanted: known ? String(known.chainId) : "the chain id of the network above",
    });
  }
  if (!/^0x[0-9a-fA-F]{40}$/.test(address)) {
    problems.push({
      name: "NEXT_PUBLIC_TRACE_CONTRACT_ADDRESS",
      found: address || "(not set)",
      wanted: "the deployed TRACE address, 0x and forty hex characters",
    });
  }
  if (problems.length > 0 || !known) return { ok: false, problems };

  return {
    ok: true,
    config: {
      network,
      chainId,
      contractAddress: address as `0x${string}`,
      explorer: known.explorer,
      rpc: known.rpc,
    },
  };
}

export const configResult: ConfigResult = read();

/** The explorer's page for one transaction, or the empty string when unset. */
export function txLink(config: AppConfig | undefined, hash: string | undefined): string {
  if (!config || !hash) return "";
  return `${config.explorer}/tx/${hash}`;
}

export function addressLink(config: AppConfig | undefined, address: string | undefined): string {
  if (!config || !address) return "";
  return `${config.explorer}/address/${address}`;
}
