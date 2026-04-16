import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-zinc-950 px-6 py-12 text-zinc-100">
      <div className="mx-auto max-w-2xl">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="text-xl">Route not found</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-zinc-300">
            <p>
              The requested Strategist console route could not be resolved. Use a governed route below to
              return to a projection-backed surface.
            </p>
            <div className="flex flex-wrap gap-2">
              <Button asChild className="rounded-xl">
                <Link href="/workboard">Open workboard</Link>
              </Button>
              <Button asChild variant="outline" className="rounded-xl border-zinc-700 bg-transparent">
                <Link href="/validator/burn-in">Open validator</Link>
              </Button>
              <Button asChild variant="outline" className="rounded-xl border-zinc-700 bg-transparent">
                <Link href="/tribunal">Open tribunal</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
