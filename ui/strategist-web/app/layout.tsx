import "./globals.css";

import type { Metadata } from "next";
import { ReactNode } from "react";

import { QueryProvider } from "@/components/providers/query-provider";
import { DomainBoundaryProvider } from "@/features/shared/domain-boundary-provider";
import { CommandReceiptLaneProvider } from "@/features/shared/command-receipts/command-receipt-lane-provider";
import { ReviewPacketLaneProvider } from "@/features/shared/review-packets/review-packet-lane-provider";
import { NotificationLaneProvider } from "@/features/shared/notifications/notification-lane-provider";

export const metadata: Metadata = {
  title: "Strategist Web",
  description: "Projection-backed institutional trading and adjudication control surface.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <DomainBoundaryProvider>
            <NotificationLaneProvider>
              <CommandReceiptLaneProvider><ReviewPacketLaneProvider>{children}</ReviewPacketLaneProvider></CommandReceiptLaneProvider>
            </NotificationLaneProvider>
          </DomainBoundaryProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
