"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { configResult } from "@/lib/config/env";
import { writeClient } from "@/lib/genlayer/client";
import {
  accountsOf,
  chainOf,
  discoverWallets,
  forgetWallet,
  rememberWallet,
  rememberedWallet,
  switchChain,
  type Wallet,
} from "@/lib/wallet/wallet";

type WalletState = {
  wallets: Wallet[];
  wallet: Wallet | undefined;
  account: string | undefined;
  chainId: number | undefined;
  wrongNetwork: boolean;
  connecting: boolean;
  problem: string | undefined;
  connect: (wallet: Wallet) => Promise<void>;
  disconnect: () => void;
  fixNetwork: () => Promise<void>;
  writeClientFor: (provider: unknown) => ReturnType<typeof writeClient>;
};

const WalletContext = createContext<WalletState | undefined>(undefined);

export function WalletProvider({ children }: { children: React.ReactNode }) {
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [wallet, setWallet] = useState<Wallet>();
  const [account, setAccount] = useState<string>();
  const [chainId, setChainId] = useState<number>();
  const [connecting, setConnecting] = useState(false);
  const [problem, setProblem] = useState<string>();

  useEffect(() => discoverWallets(setWallets), []);

  const attach = useCallback(async (found: Wallet, ask: boolean) => {
    const accounts = await accountsOf(found.provider, ask);
    if (accounts.length === 0) return false;
    setWallet(found);
    setAccount(accounts[0]);
    setChainId(await chainOf(found.provider));
    rememberWallet(found.info.rdns);
    return true;
  }, []);

  // reconnect silently to the wallet this browser used last, if it still
  // remembers this site; a wallet that announces late is picked up here too
  useEffect(() => {
    const chosen = rememberedWallet();
    if (!chosen || wallet) return;
    const found = wallets.find((w) => w.info.rdns === chosen);
    if (found) void attach(found, false).catch(() => undefined);
  }, [wallets, wallet, attach]);

  useEffect(() => {
    if (!wallet?.provider.on) return;
    const onAccounts = (payload: unknown) => {
      const accounts = payload as string[];
      if (!accounts || accounts.length === 0) {
        setAccount(undefined);
        setWallet(undefined);
        forgetWallet();
      } else {
        setAccount(accounts[0]);
      }
    };
    const onChain = (payload: unknown) => {
      const raw = payload as string;
      setChainId(typeof raw === "string" ? Number.parseInt(raw, 16) : Number(raw));
    };
    wallet.provider.on("accountsChanged", onAccounts);
    wallet.provider.on("chainChanged", onChain);
    return () => {
      wallet.provider.removeListener?.("accountsChanged", onAccounts);
      wallet.provider.removeListener?.("chainChanged", onChain);
    };
  }, [wallet]);

  const connect = useCallback(
    async (found: Wallet) => {
      setConnecting(true);
      setProblem(undefined);
      try {
        const attached = await attach(found, true);
        if (!attached) setProblem("That wallet did not offer an account.");
      } catch (err) {
        const code = (err as { code?: number })?.code;
        setProblem(code === 4001 ? "You declined the connection." : "That wallet did not connect.");
      } finally {
        setConnecting(false);
      }
    },
    [attach],
  );

  const disconnect = useCallback(() => {
    setWallet(undefined);
    setAccount(undefined);
    setChainId(undefined);
    forgetWallet();
  }, []);

  const fixNetwork = useCallback(async () => {
    if (!wallet || !configResult.ok) return;
    const { chainId: wanted, rpc, explorer } = configResult.config;
    try {
      await switchChain(wallet.provider, wanted, rpc, explorer);
      setChainId(await chainOf(wallet.provider));
    } catch {
      setProblem("Your wallet did not switch networks. Switch it yourself and try again.");
    }
  }, [wallet]);

  const value = useMemo<WalletState>(
    () => ({
      wallets,
      wallet,
      account,
      chainId,
      wrongNetwork:
        Boolean(account) && configResult.ok && chainId !== undefined &&
        chainId !== configResult.config.chainId,
      connecting,
      problem,
      connect,
      disconnect,
      fixNetwork,
      writeClientFor: writeClient,
    }),
    [wallets, wallet, account, chainId, connecting, problem, connect, disconnect, fixNetwork],
  );

  return <WalletContext.Provider value={value}>{children}</WalletContext.Provider>;
}

export function useWallet(): WalletState {
  const value = useContext(WalletContext);
  if (!value) throw new Error("useWallet must be used inside WalletProvider");
  return value;
}
