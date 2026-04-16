"use client";

import { AlertTriangle, Bell, Info, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useNotificationLane } from "@/features/shared/notifications/notification-lane-provider";

function iconFor(kind: string) {
  if (kind === "error") return <XCircle className="h-4 w-4 text-rose-300" />;
  if (kind === "warning") return <AlertTriangle className="h-4 w-4 text-amber-300" />;
  return <Info className="h-4 w-4 text-sky-300" />;
}

export function NotificationLane() {
  const { notifications, dismissNotification, clearNotifications } = useNotificationLane();

  if (!notifications.length) return null;

  return (
    <div className="mb-6 rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-sm font-medium text-zinc-100">
            <Bell className="h-4 w-4 text-amber-300" /> Shell notifications
          </div>
          <div className="text-xs text-zinc-400">Freshness, drift, and console-state warnings that should stay visible across routes.</div>
        </div>
        <Button variant="outline" className="border-zinc-700 bg-transparent text-xs" onClick={clearNotifications}>
          Clear notifications
        </Button>
      </div>
      <div className="space-y-3">
        {notifications.map((notification) => (
          <div key={notification.id} className="flex items-start justify-between gap-3 rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 text-sm font-medium text-zinc-100">
                {iconFor(notification.kind)}
                {notification.title}
              </div>
              <div className="mt-1 text-sm text-zinc-300">{notification.message}</div>
              <div className="mt-2 text-xs text-zinc-500">{notification.created_at_utc}</div>
            </div>
            <Button variant="ghost" className="h-8 rounded-full px-3 text-xs text-zinc-400 hover:text-zinc-100" onClick={() => dismissNotification(notification.id)}>
              dismiss
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
