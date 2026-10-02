import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center gap-6 p-6">
      <div>
        <h1 className="text-4xl font-bold">Scout</h1>
        <p className="text-scout-muted">Autonomous shelf-void detection & micro-audit intelligence.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Link href="/dashboard" className="rounded-xl border border-scout-border bg-scout-surface p-6 hover:border-scout-alert">
          <h2 className="text-xl font-semibold">Store Manager Portal</h2>
          <p className="text-sm text-scout-muted">KPIs, revenue recovered, velocity anomalies.</p>
        </Link>
        <Link href="/floor" className="rounded-xl border border-scout-border bg-scout-surface p-6 hover:border-scout-alert">
          <h2 className="text-xl font-semibold">Floor Staff PWA</h2>
          <p className="text-sm text-scout-muted">The 3-minute morning audit checklist.</p>
        </Link>
      </div>
      <Link href="/simulate" className="rounded-lg bg-scout-aiBg p-3 text-center text-sm font-medium text-scout-ai">
        Judges Demo Playground →
      </Link>
    </main>
  );
}
