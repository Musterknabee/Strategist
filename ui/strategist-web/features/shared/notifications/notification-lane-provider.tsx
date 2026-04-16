"use client";

import { createContext, ReactNode, useContext, useMemo, useState } from "react";

export type ShellNotification = {
  id: string;
  kind: "info" | "warning" | "error";
  title: string;
  message: string;
  created_at_utc: string;
  dedupe_key?: string;
};

type NotificationLaneState = {
  notifications: ShellNotification[];
  pushNotification: (notification: ShellNotification) => void;
  dismissNotification: (id: string) => void;
  clearNotifications: () => void;
};

const NotificationLaneContext = createContext<NotificationLaneState>({
  notifications: [],
  pushNotification: () => undefined,
  dismissNotification: () => undefined,
  clearNotifications: () => undefined,
});

export function NotificationLaneProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<ShellNotification[]>([]);

  const value = useMemo<NotificationLaneState>(
    () => ({
      notifications,
      pushNotification: (notification) => {
        setNotifications((current) => {
          const withoutDupes = notification.dedupe_key
            ? current.filter((entry) => entry.dedupe_key !== notification.dedupe_key)
            : current;
          return [notification, ...withoutDupes].slice(0, 6);
        });
      },
      dismissNotification: (id) => setNotifications((current) => current.filter((entry) => entry.id !== id)),
      clearNotifications: () => setNotifications([]),
    }),
    [notifications],
  );

  return <NotificationLaneContext.Provider value={value}>{children}</NotificationLaneContext.Provider>;
}

export function useNotificationLane() {
  return useContext(NotificationLaneContext);
}
