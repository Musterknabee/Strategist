import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { getFrontendDiagnosticsManifest } from "@/lib/diagnostics";

export default function SettingsChecklistPage() {
  const manifest = getFrontendDiagnosticsManifest();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-zinc-100">Setup checklist</h2>
        <p className="mt-1 text-sm text-zinc-400">
          Copy-friendly local commands for bringing up the Strategist web shell with either a live backend or a forced mock posture.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {manifest.commands.map((item) => (
          <Card key={item.label} className="border-zinc-800 bg-zinc-900">
            <CardHeader>
              <CardTitle className="text-base text-zinc-100">{item.label}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-zinc-400">{item.description}</p>
              <CopyCommandBlock command={item.command} />
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader>
          <CardTitle className="text-base text-zinc-100">Bring-up guidance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-zinc-300">
          {manifest.guidance.map((line) => (
            <p key={line}>• {line}</p>
          ))}
          <p>• Recommended local order: bootstrap env → doctor → dev server → smoke → check → build.</p>
        </CardContent>
      </Card>
    </div>
  );
}
