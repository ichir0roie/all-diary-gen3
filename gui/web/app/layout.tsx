import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import AuthGate from "@/components/AuthGate";
import Nav from "@/components/Nav";
import { T } from "@/lib/text";

export const metadata: Metadata = {
  title: T.appName,
  description: T.appDescription,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <AuthGate>
          <Nav />
          <main>{children}</main>
        </AuthGate>
      </body>
    </html>
  );
}
