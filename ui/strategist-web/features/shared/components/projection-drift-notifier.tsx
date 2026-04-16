"use client";

import { useEffect } from "react";

import { useNotificationLane } from "@/features/shared/notifications/notification-lane-provider";

export function ProjectionDriftNotifier({
  active,
  dedupeKey,
  title,
  message,
}: {
  active: boolean;
  dedupeKey: string;
  title: string;
  message: string;
}) {
  const { pushNotification } = useNotificationLane();

  useEffect(() => {
    if (!active) return;
    pushNotification({
      id: `${dedupeKey}-${new Date().toISOString()}`,
      dedupe_key: dedupeKey,
      kind: "warning",
      title,
      message,
      created_at_utc: new Date().toISOString(),
    });
  }, [active, dedupeKey, message, pushNotification, title]);

  return null;
}
