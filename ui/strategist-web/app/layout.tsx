import type { Metadata } from "next";
import { TerminalShell } from "@/components/terminal/TerminalShell";
import { AppQueryProvider } from "@/components/providers/AppQueryProvider";
import { TerminalCockpitProvider } from "@/lib/terminal/cockpit-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "SV·TERM",
  description: "Strategy Validator Terminal · read-plane operator cockpit",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppQueryProvider>
          <TerminalCockpitProvider>
            <TerminalShell>{children}</TerminalShell>
          </TerminalCockpitProvider>
        </AppQueryProvider>
      </body>
    </html>
  );
}
