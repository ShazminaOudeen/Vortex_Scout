import Link from "next/link";
import {
  LayoutDashboard,
  Smartphone,
  Boxes,
  Award,
  Cpu,
  ArrowRight,
  Sparkles,
} from "lucide-react";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center gap-8 p-6">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-3 py-1 text-xs font-bold text-violet-600">
          <Sparkles className="h-3.5 w-3.5" />
          Autonomous Shelf-Void Intelligence
        </div>
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight text-zinc-900">
          Vortex Scout
        </h1>
        <p className="text-base text-zinc-600 max-w-2xl">
          Real-time phantom stockout detection, Bayesian velocity profiling, and autonomous micro-audit routing for modern retail stores.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Link
          href="/dashboard"
          className="group rounded-2xl border border-scout-border bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:border-violet-500 hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <div className="rounded-xl bg-violet-50 p-2.5 text-violet-600 border border-violet-100">
              <LayoutDashboard className="h-5 w-5" />
            </div>
            <ArrowRight className="h-4 w-4 text-zinc-400 group-hover:text-violet-600 group-hover:translate-x-0.5 transition-all" />
          </div>
          <h2 className="mt-4 text-lg font-bold text-zinc-900">Store Manager Portal</h2>
          <p className="mt-1 text-xs text-zinc-500">
            Real KPIs, revenue recovered, live velocity curves, and store audit feeds.
          </p>
        </Link>

        <Link
          href="/floor"
          className="group rounded-2xl border border-scout-border bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:border-emerald-500 hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <div className="rounded-xl bg-emerald-50 p-2.5 text-emerald-600 border border-emerald-100">
              <Smartphone className="h-5 w-5" />
            </div>
            <ArrowRight className="h-4 w-4 text-zinc-400 group-hover:text-emerald-600 group-hover:translate-x-0.5 transition-all" />
          </div>
          <h2 className="mt-4 text-lg font-bold text-zinc-900">Floor Staff PWA</h2>
          <p className="mt-1 text-xs text-zinc-500">
            Mobile 3-minute morning audit checklist, aisle routing, and one-tap restock writeback.
          </p>
        </Link>

        <Link
          href="/evaluation"
          className="group rounded-2xl border border-scout-border bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:border-teal-500 hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <div className="rounded-xl bg-teal-50 p-2.5 text-teal-600 border border-teal-100">
              <Award className="h-5 w-5" />
            </div>
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
              New: F3/F4
            </span>
          </div>
          <h2 className="mt-4 text-lg font-bold text-zinc-900">Model Evaluation Hub</h2>
          <p className="mt-1 text-xs text-zinc-500">
            Empirical benchmark: Scout Ensemble vs. Naive Rules across 200 catalog SKUs.
          </p>
        </Link>

        <Link
          href="/inventory"
          className="group rounded-2xl border border-scout-border bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:border-blue-500 hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <div className="rounded-xl bg-blue-50 p-2.5 text-blue-600 border border-blue-100">
              <Boxes className="h-5 w-5" />
            </div>
            <ArrowRight className="h-4 w-4 text-zinc-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
          </div>
          <h2 className="mt-4 text-lg font-bold text-zinc-900">Inventory Explorer</h2>
          <p className="mt-1 text-xs text-zinc-500">
            200-SKU search, category filtering, shelf-void risk tiers, and SKU detail views.
          </p>
        </Link>

        <Link
          href="/simulate"
          className="group sm:col-span-2 rounded-2xl border border-violet-200 bg-gradient-to-r from-violet-500/10 via-purple-500/5 to-transparent p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:border-violet-500 hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <div className="rounded-xl bg-violet-600 p-2.5 text-white shadow-sm">
              <Cpu className="h-5 w-5" />
            </div>
            <span className="rounded-full bg-violet-600 px-2.5 py-0.5 text-xs font-bold text-white">
              Judges Demo Playground →
            </span>
          </div>
          <h2 className="mt-4 text-lg font-bold text-zinc-900">Interactive Simulation Hub & Live POS Terminal</h2>
          <p className="mt-1 text-xs text-zinc-600">
            Inject frozen stockouts, damaged write-offs, trigger the Gemini AI agent, and watch the live streaming POS feed.
          </p>
        </Link>
      </div>
    </main>
  );
}
