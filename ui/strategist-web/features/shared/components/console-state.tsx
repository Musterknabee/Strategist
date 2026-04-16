"use client";

import { AlertTriangle, Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function ConsoleLoadingState({ title, message }: { title: string; message: string }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base text-zinc-100">
          <Loader2 className="h-4 w-4 animate-spin text-emerald-300" /> {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-zinc-400">{message}</CardContent>
    </Card>
  );
}

export function ConsoleErrorState({ title, message }: { title: string; message: string }) {
  return (
    <Card className="border-amber-500/30 bg-zinc-900">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base text-amber-200">
          <AlertTriangle className="h-4 w-4" /> {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-zinc-300">
        <div>{message}</div>
        <Button variant="outline" className="border-zinc-700 bg-transparent text-xs" onClick={() => window.location.reload()}>
          Reload console surface
        </Button>
      </CardContent>
    </Card>
  );
}
