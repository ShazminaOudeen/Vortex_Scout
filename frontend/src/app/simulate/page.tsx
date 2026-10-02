"use client";
import { useState } from "react";
import { api } from "@/lib/api";

// Judge demo hub. TODO(Task 3/4): live POS terminal stream, dark-mode toggle.
export default function SimulatePage() {
  const [log, setLog] = useState<string[]>([]);
  const push = (m: string) => setLog((l) => [...l.slice(-30), `${new Date().toLocaleTimeString()}  ${m}`]);

  async function run(label: string, fn: () => Promise<unknown>) {
    push(`> ${label}`);
    try { push(JSON.stringify(await fn())); } catch (e) { push(`ERROR ${(e as Error).message}`); }
  }

  const btn = "rounded-lg bg-scout-violet px-4 py-3 text-sm font-semibold text-white hover:opacity-90";
  return (
    <main className="min-h-screen bg-scout-night p-6 text-zinc-100">
      <h1 className="mb-4 text-2xl font-bold">Simulation Hub</h1>
      <div className="flex flex-wrap gap-3">
        <button className={btn} onClick={() => run("inject phantom stockout", () => api.injectScenario("phantom"))}>Inject Phantom Stockout</button>
        <button className={btn} onClick={() => run("simulate normal peak", () => api.injectScenario("normal"))}>Simulate Normal Peak</button>
        <button className={btn} onClick={() => run("reset store", () => api.injectScenario("reset"))}>Reset Store State</button>
        <button className="rounded-lg bg-scout-neon px-4 py-3 text-sm font-semibold text-white" onClick={() => run("run detection", api.runDetection)}>
          Run Scout Detection &amp; Trigger Agent
        </button>
      </div>
      <pre className="mt-6 h-80 overflow-auto rounded-lg bg-black p-4 font-mono text-xs text-emerald-400">
        {log.join("\n") || "Awaiting events…"}
      </pre>
    </main>
  );
}
