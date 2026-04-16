import type { ReactElement, ReactNode } from "react";
import { render } from "@testing-library/react";

import { DomainBoundaryProvider } from "@/features/shared/domain-boundary-provider";
import { NotificationLaneProvider } from "@/features/shared/notifications/notification-lane-provider";
import { CommandReceiptLaneProvider } from "@/features/shared/command-receipts/command-receipt-lane-provider";
import { ReviewPacketLaneProvider } from "@/features/shared/review-packets/review-packet-lane-provider";

function TestProviders({ children }: { children: ReactNode }) {
  return (
    <DomainBoundaryProvider>
      <NotificationLaneProvider>
        <CommandReceiptLaneProvider>
          <ReviewPacketLaneProvider>{children}</ReviewPacketLaneProvider>
        </CommandReceiptLaneProvider>
      </NotificationLaneProvider>
    </DomainBoundaryProvider>
  );
}

export function renderWithProviders(ui: ReactElement) {
  return render(ui, { wrapper: TestProviders });
}
