/**
 * The person's own wallet, discovered the way browsers agreed to do it.
 *
 * EIP-6963: wallets announce themselves, the page listens. No custom protocol,
 * no key in this console, and no assumption that a single injected provider is
 * the only one installed.
 */

export type WalletInfo = { uuid: string; name: string; icon: string; rdns: string };
export type Wallet = { info: WalletInfo; provider: Eip1193Provider };

export type Eip1193Provider = {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  on?: (event: string, handler: (payload: unknown) => void) => void;
  removeListener?: (event: string, handler: (payload: unknown) => void) => void;
};

const CHOSEN = "trace.wallet.rdns";

/**
 * Listen for wallets, and ask the ones already loaded to announce themselves.
 * The listener stays attached: a wallet that announces late still arrives.
 */
export function discoverWallets(onFound: (wallets: Wallet[]) => void): () => void {
  if (typeof window === "undefined") return () => {};
  const found = new Map<string, Wallet>();

  const handler = (event: Event) => {
    const detail = (event as CustomEvent).detail as Wallet | undefined;
    if (!detail?.info?.rdns || !detail.provider) return;
    found.set(detail.info.rdns, detail);
    onFound([...found.values()]);
  };

  window.addEventListener("eip6963:announceProvider", handler as EventListener);
  window.dispatchEvent(new Event("eip6963:requestProvider"));
  return () => window.removeEventListener("eip6963:announceProvider", handler as EventListener);
}

export function rememberWallet(rdns: string) {
  try {
    window.localStorage.setItem(CHOSEN, rdns);
  } catch {
    /* a browser that refuses storage still works; it just asks again */
  }
}

export function forgetWallet() {
  try {
    window.localStorage.removeItem(CHOSEN);
  } catch {
    /* as above */
  }
}

export function rememberedWallet(): string | null {
  try {
    return window.localStorage.getItem(CHOSEN);
  } catch {
    return null;
  }
}

export async function accountsOf(provider: Eip1193Provider, ask: boolean): Promise<string[]> {
  const method = ask ? "eth_requestAccounts" : "eth_accounts";
  const accounts = (await provider.request({ method })) as string[] | undefined;
  return Array.isArray(accounts) ? accounts : [];
}

export async function chainOf(provider: Eip1193Provider): Promise<number> {
  const chain = (await provider.request({ method: "eth_chainId" })) as string | number;
  return typeof chain === "string" ? Number.parseInt(chain, 16) : Number(chain);
}

/**
 * Ask the wallet to move to the chain this console is configured for. A wallet
 * that does not know the chain is offered its details once.
 */
export async function switchChain(
  provider: Eip1193Provider,
  chainId: number,
  rpc: string,
  explorer: string,
): Promise<void> {
  const hex = `0x${chainId.toString(16)}`;
  try {
    await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId: hex }] });
  } catch (err) {
    const code = (err as { code?: number })?.code;
    if (code !== 4902) throw err;
    await provider.request({
      method: "wallet_addEthereumChain",
      params: [
        {
          chainId: hex,
          chainName: "GenLayer StudioNet",
          nativeCurrency: { name: "GEN", symbol: "GEN", decimals: 18 },
          rpcUrls: [rpc],
          blockExplorerUrls: [explorer],
        },
      ],
    });
  }
}
