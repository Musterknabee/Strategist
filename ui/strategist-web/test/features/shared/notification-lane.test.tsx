import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { NotificationLane } from "@/features/shared/components/notification-lane";

vi.mock("@/features/shared/notifications/notification-lane-provider", () => ({
  useNotificationLane: () => ({
    notifications: [
      { id: "n1", title: "Runtime drift", message: "Read-plane is stale.", tone: "warning" },
    ],
    dismissNotification: vi.fn(),
    clearNotifications: vi.fn(),
  }),
}));

describe("NotificationLane", () => {
  it("renders shared shell notifications", () => {
    render(<NotificationLane />);
    expect(screen.getByText(/runtime drift/i)).toBeInTheDocument();
    expect(screen.getByText(/read-plane is stale/i)).toBeInTheDocument();
  });
});
