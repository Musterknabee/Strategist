"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { createStrategistQueryClient } from "@/lib/query/query-client";

export function AppQueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(() => createStrategistQueryClient());
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
