import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "outline";
};

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs",
        variant === "outline"
          ? "border-zinc-700 bg-transparent text-zinc-300"
          : "border-zinc-700 bg-zinc-900 text-zinc-300",
        className,
      )}
      {...props}
    />
  );
}
