import { UI_FACADE_PATH } from "@/lib/contracts/facade";

export default function HomePage() {
  return (
    <main>
      <h1>Strategist</h1>
      <p>
        Operator console shell. Reads bind to backend{" "}
        <code>/ui/*</code> routes; facade metadata at{" "}
        <code>{UI_FACADE_PATH}</code>.
      </p>
    </main>
  );
}
