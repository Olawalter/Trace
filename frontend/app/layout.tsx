import type { Metadata } from "next";
import localFont from "next/font/local";

import "./globals.css";
import { AppFrame } from "@/components/ui/app-frame";

// Read off disk, not fetched from a font CDN while the site builds. See
// app/fonts/README.md: a build that needs somebody else's service to finish is
// a build that can fail for reasons nothing in this repository can explain.
//
// The serif is display only and stays at 400 at every size; the grotesque
// carries all body and UI text; the mono is reserved for identifiers and hashes.
const serif = localFont({
  src: "./fonts/instrument-serif-400.woff2",
  weight: "400",
  style: "normal",
  variable: "--font-serif-display",
  display: "swap",
});

const sans = localFont({
  src: "./fonts/schibsted-grotesk-variable.woff2",
  weight: "400 800",
  style: "normal",
  variable: "--font-sans-ui",
  display: "swap",
});

const mono = localFont({
  src: "./fonts/azeret-mono-variable.woff2",
  weight: "400 500",
  style: "normal",
  variable: "--font-mono-data",
  display: "swap",
});

export const metadata: Metadata = {
  title: "TRACE: verifiable compliance protocols",
  description:
    "Define what must be true. Submit evidence. Let GenLayer independently verify whether the " +
    "evidence satisfies the protocol.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${serif.variable} ${sans.variable} ${mono.variable}`}>
      <body>
        <AppFrame>{children}</AppFrame>
      </body>
    </html>
  );
}
