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
      <header className="sticky top-0 z-20 border-b bg-[var(--background)]/92 backdrop-blur">
        {/* on a phone the nav takes a row of its own: squeezed between the
            wordmark and the wallet it collapses to a couple of clipped letters */}
        <div className="shell grid grid-cols-[auto_1fr] items-center gap-x-4 gap-y-2 py-3
                        md:flex md:h-[72px] md:gap-8 md:py-0">
          <Link href="/" className="flex shrink-0 items-baseline gap-2.5" aria-label="TRACE, home">
            <Mark className="h-7 w-7 self-center" />
            <span className="font-serif text-[26px] leading-none tracking-[-0.015em]">Trace</span>
          </Link>
          <div className="justify-self-end md:order-last">
            <WalletButton />
          </div>
          <nav className="no-scrollbar col-span-2 flex min-w-0 gap-1 overflow-x-auto
                          md:col-span-1 md:flex-1"
               aria-label="Sections">
            {NAV.map((item) => (
              <Link key={item.href} href={item.href}
                    aria-current={active(item.href) ? "page" : undefined}
                    className={`shrink-0 rounded-full px-3.5 py-1.5 text-sm transition-colors ${
                      active(item.href)
                        ? "bg-[var(--surface)] text-[var(--text)]"
                        : "text-[var(--muted)] hover:text-[var(--text)]"}`}>
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main className="shell flex-1 py-12 md:py-16">{children}</main>

      <footer className="rule mt-20">
        <div className="shell grid gap-4 py-10 md:grid-cols-[1fr_auto] md:items-end">
          <p className="max-w-lg text-sm text-[var(--muted)]">
            Verification by GenLayer consensus. The contract is authoritative; this console shows
            what it holds and signs nothing by itself.
          </p>
          {configResult.ok ? (
            <p className="text-xs text-[var(--faint)] md:text-right">
              StudioNet, chain {configResult.config.chainId}
              <br />
              <a className="mono hover:text-[var(--text)]"
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
