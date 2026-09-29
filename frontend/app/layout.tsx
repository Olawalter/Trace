import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";

import "./globals.css";
import { AppFrame } from "@/components/ui/app-frame";

export const metadata: Metadata = {
  title: "TRACE: verifiable compliance protocols",
  description:
    "Define what must be true. Submit evidence. Let GenLayer independently verify whether the " +
    "evidence satisfies the protocol.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body>
        <AppFrame>{children}</AppFrame>
      </body>
    </html>
  );
}
