"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { configResult } from "@/lib/config/env";
import { WalletButton } from "@/components/wallet/wallet-button";
import { Mark } from "@/components/ui/mark";
import { WalletProvider } from "@/components/wallet/wallet-provider";

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/protocols", label: "Protocols" },
  { href: "/verifications", label: "Verifications" },
  { href: "/activity", label: "Activity" },
];

export function AppFrame({ children }: { children: React.ReactNode }) {
  return (
    <WalletProvider>
      <Frame>{children}</Frame>
    </WalletProvider>
  );
}

function Frame({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const active = (href: string) => (href === "/" ? path === "/" : path.startsWith(href));

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b bg-[var(--background)]/95 backdrop-blur">
        <div className="shell flex h-14 items-center gap-6">
          <Link href="/" className="flex shrink-0 items-center gap-2" aria-label="TRACE, home">
            <Mark className="h-6 w-6" />
            <span className="text-[15px] font-semibold tracking-[0.18em]">TRACE</span>
          </Link>
          <nav className="no-scrollbar flex min-w-0 flex-1 gap-1 overflow-x-auto"
               aria-label="Sections">
            {NAV.map((item) => (
              <Link key={item.href} href={item.href}
                    aria-current={active(item.href) ? "page" : undefined}
                    className={`shrink-0 rounded-sm px-2.5 py-1 text-sm ${
                      active(item.href)
                        ? "text-[var(--text)]"
                        : "text-[var(--muted)] hover:text-[var(--text)]"}`}>
                {item.label}
              </Link>
            ))}
          </nav>
          <WalletButton />
        </div>
      </header>

      <main className="shell flex-1 py-8">{children}</main>

      <footer className="rule mt-10">
        <div className="shell flex flex-wrap items-center justify-between gap-3 py-5 text-xs
                        text-[var(--muted)]">
          <p>
            Verification by GenLayer consensus. The contract is authoritative; this console shows
            what it holds and signs nothing by itself.
          </p>
          {configResult.ok ? (
            <p className="mono">
              StudioNet · chain {configResult.config.chainId} ·{" "}
              <a className="underline decoration-dotted underline-offset-2"
                 href={`${configResult.config.explorer}/address/${configResult.config.contractAddress}`}
                 target="_blank" rel="noreferrer">
                {configResult.config.contractAddress}
              </a>
            </p>
          ) : null}
        </div>
      </footer>
    </div>
  );
}
