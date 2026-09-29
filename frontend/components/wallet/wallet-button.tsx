"use client";

import { useState } from "react";
import { AlertTriangle, Wallet as WalletIcon } from "lucide-react";

import { configResult } from "@/lib/config/env";
import { shortAddress } from "@/lib/formatting/present";
import { useWallet } from "@/components/wallet/wallet-provider";

export function WalletButton() {
  const { wallets, account, wrongNetwork, connecting, problem, connect, disconnect, fixNetwork } =
    useWallet();
  const [open, setOpen] = useState(false);

  if (!configResult.ok) return null;

  if (account) {
    return (
      <div className="flex shrink-0 items-center gap-2">
        {wrongNetwork ? (
          <button type="button" className="btn text-[var(--warning)]" onClick={() => void fixNetwork()}>
            <AlertTriangle className="h-4 w-4" aria-hidden />
            Wrong network
          </button>
        ) : null}
        <span className="mono hidden text-xs text-[var(--muted)] sm:inline">
          {shortAddress(account)}
        </span>
        <button type="button" className="btn" onClick={disconnect}>
          Disconnect
        </button>
      </div>
    );
  }

  return (
    <div className="relative shrink-0">
      <button type="button" className="btn btn-primary" onClick={() => setOpen((v) => !v)}
              aria-expanded={open} aria-haspopup="dialog" disabled={connecting}>
        <WalletIcon className="h-4 w-4" aria-hidden />
        {connecting ? "Connecting…" : "Connect wallet"}
      </button>

      {open ? (
        <div role="dialog" aria-label="Choose a wallet"
             className="card absolute right-0 z-30 mt-2 w-72 p-3">
          <h2 className="text-sm font-semibold">Connect a wallet</h2>
          <p className="mt-1 text-xs text-[var(--muted)]">
            TRACE signs with your own browser wallet. It never asks for, sees or stores a private
            key.
          </p>
          <ul className="mt-3 grid gap-1">
            {wallets.length === 0 ? (
              <li className="text-xs text-[var(--muted)]">
                No wallet announced itself. Install one, or unlock the one you have, and reopen this.
              </li>
            ) : (
              wallets.map((wallet) => (
                <li key={wallet.info.rdns}>
                  <button type="button"
                          className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left
                                     text-sm hover:bg-[var(--surface)]"
                          onClick={async () => {
                            await connect(wallet);
                            setOpen(false);
                          }}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={wallet.info.icon} alt="" className="h-5 w-5 rounded" />
                    {wallet.info.name}
                  </button>
                </li>
              ))
            )}
          </ul>
          {problem ? <p className="mt-2 text-xs text-[var(--error)]">{problem}</p> : null}
          <button type="button" className="mt-3 text-xs text-[var(--muted)] underline"
                  onClick={() => setOpen(false)}>
            Close
          </button>
        </div>
      ) : null}
    </div>
  );
}
