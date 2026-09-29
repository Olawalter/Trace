import type { Metadata } from "next";
import { Instrument_Serif, Schibsted_Grotesk, Azeret_Mono } from "next/font/google";

import "./globals.css";
import { AppFrame } from "@/components/ui/app-frame";

// The serif is display only and stays at 400 at every size; the grotesque
// carries all body and UI text; the mono is reserved for identifiers and hashes.
const serif = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-serif-display",
  display: "swap",
});

const sans = Schibsted_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans-ui",
  display: "swap",
});

const mono = Azeret_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
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
