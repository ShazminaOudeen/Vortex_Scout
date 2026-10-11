"use client";
import Link from "next/link";
import { CheckCircle2, RefreshCw, BarChart2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface AllClearScreenProps {
  totalResolved: number;
  totalRevenue?: number;
  onRefresh: () => void;
  onResetSession: () => void;
}

export function AllClearScreen({
  totalResolved,
  totalRevenue = 0,
  onRefresh,
  onResetSession,
}: AllClearScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-emerald-500/20 bg-gradient-to-b from-emerald-500/10 via-scout-surface to-scout-surface p-6 text-center shadow-lg">
      <div className="relative mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-emerald-500/20 ring-8 ring-emerald-500/10">
        <CheckCircle2 className="h-10 w-10 text-emerald-500 animate-in zoom-in-75 duration-300" />
      </div>

      <h2 className="text-xl font-bold tracking-tight text-zinc-900">
        All Shelves Verified ✓
      </h2>
      <p className="mt-1 text-sm text-scout-muted max-w-xs">
        {totalResolved > 0
          ? `All ${totalResolved} potential shelf-voids have been physically audited and reconciled with store ledgers.`
          : "Zero phantom voids detected. Store shelves and inventory records are perfectly in sync."}
      </p>

      {totalResolved > 0 && (
        <div className="mt-5 grid grid-cols-2 gap-3 w-full max-w-xs">
          <div className="rounded-xl border border-scout-border bg-scout-bg/60 p-3">
            <p className="text-xs text-scout-muted uppercase font-semibold">Audited</p>
            <p className="text-lg font-bold text-zinc-900">{totalResolved} items</p>
          </div>
          <div className="rounded-xl border border-scout-border bg-scout-bg/60 p-3">
            <p className="text-xs text-scout-muted uppercase font-semibold">Value Protected</p>
            <p className="text-lg font-bold text-emerald-600">
              LKR {Math.round(totalRevenue).toLocaleString()}
            </p>
          </div>
        </div>
      )}

      <div className="mt-6 flex flex-col gap-2.5 w-full max-w-xs">
        <Button
          variant="primary"
          onClick={onRefresh}
          className="flex items-center justify-center gap-2 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium"
        >
          <RefreshCw className="h-4 w-4" />
          Check for New Alerts
        </Button>

        <div className="flex gap-2">
          <Link href="/dashboard" className="flex-1">
            <Button variant="ghost" className="w-full text-xs flex items-center justify-center gap-1.5 py-2">
              <BarChart2 className="h-3.5 w-3.5" />
              Manager Portal
            </Button>
          </Link>
          <Button
            variant="ghost"
            onClick={onResetSession}
            className="text-xs flex items-center justify-center gap-1.5 py-2 text-zinc-500 hover:text-zinc-700"
            title="Reset audit session for demo"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset Demo
          </Button>
        </div>
      </div>
    </div>
  );
}
