"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  Terminal,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Trash2,
  RefreshCw,
  Search,
  Radio,
  ArrowDownCircle,
  AlertTriangle,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import type { PosTransactionFeedItem } from "@/lib/types";

interface PosTerminalProps {
  scenarioNotice?: string | null;
}

export function PosTerminal({ scenarioNotice }: PosTerminalProps) {
  const [transactions, setTransactions] = useState<PosTransactionFeedItem[]>([]);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [pollIntervalMs, setPollIntervalMs] = useState<number>(2500);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(false);
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [txRate, setTxRate] = useState<number>(18);
  const [totalVolLkr, setTotalVolLkr] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const terminalBodyRef = useRef<HTMLDivElement>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);

  // Web Audio click/beep synthesizer for retail checkout sound effect
  const playCheckoutBlip = useCallback(() => {
    if (!soundEnabled) return;
    try {
      if (!audioCtxRef.current) {
        const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        audioCtxRef.current = new AudioCtx();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === "suspended") {
        ctx.resume();
      }
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(1400, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1800, ctx.currentTime + 0.05);

      gain.gain.setValueAtTime(0.04, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.06);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.06);
    } catch {
      // AudioContext unavailable or blocked by browser policy
    }
  }, [soundEnabled]);

  // Fetch initial/recent transactions
  const fetchFeed = useCallback(async () => {
    try {
      setIsLoading(true);
      const items = await api.getRecentTransactions(50);
      setTransactions((prev) => {
        // Find newly arrived transactions
        const existingIds = new Set(prev.map((t) => t.id));
        const brandNew = items.filter((t) => !existingIds.has(t.id));

        if (brandNew.length > 0 && prev.length > 0) {
          playCheckoutBlip();
        }

        // Keep rolling buffer of newest transactions
        const merged = [...items];
        return merged.slice(0, 75);
      });

      // Compute statistics
      const total = items.reduce((sum, item) => sum + item.total_amount, 0);
      setTotalVolLkr(total);
      setTxRate(Math.max(12, Math.min(48, Math.round(items.length * 0.7))));
    } catch {
      // API may be refreshing
    } finally {
      setIsLoading(false);
    }
  }, [playCheckoutBlip]);

  // Polling stream effect
  useEffect(() => {
    fetchFeed();
    if (!isPlaying) return;

    const timer = setInterval(() => {
      fetchFeed();
    }, pollIntervalMs);

    return () => clearInterval(timer);
  }, [fetchFeed, isPlaying, pollIntervalMs]);

  // Auto-scroll to top or bottom
  useEffect(() => {
    if (autoScroll && terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = 0;
    }
  }, [transactions, autoScroll]);

  const filtered = transactions.filter((t) => {
    if (!searchTerm) return true;
    const s = searchTerm.toLowerCase();
    return (
      t.sku_id.toLowerCase().includes(s) ||
      t.sku_name.toLowerCase().includes(s) ||
      t.aisle.toLowerCase().includes(s) ||
      t.bay.toLowerCase().includes(s) ||
      t.store_id.toLowerCase().includes(s)
    );
  });

  return (
    <div className="flex flex-col rounded-xl border border-emerald-500/30 bg-black/95 shadow-2xl backdrop-blur-md overflow-hidden">
      {/* Terminal Title Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-500/20 bg-zinc-950/90 px-4 py-3">
        {/* Left: Indicator & Status */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full bg-red-500/80 inline-block" />
            <span className="h-3 w-3 rounded-full bg-yellow-500/80 inline-block" />
            <span className="h-3 w-3 rounded-full bg-emerald-500/80 inline-block" />
          </div>
          <div className="flex items-center gap-2 font-mono text-xs font-semibold text-emerald-400">
            <Terminal className="h-4 w-4 text-emerald-400" />
            <span>POS TELEMETRY TERMINAL</span>
            <span className="rounded bg-emerald-950/80 px-1.5 py-0.5 text-[10px] text-emerald-300 border border-emerald-600/30">
              STORE_01
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-xs">
            <span
              className={`h-2 w-2 rounded-full ${
                isPlaying ? "animate-pulse bg-emerald-400" : "bg-zinc-600"
              }`}
            />
            <span className="font-mono text-[11px] text-zinc-400">
              {isPlaying ? "LIVE STREAMING" : "STREAM PAUSED"}
            </span>
          </div>
        </div>

        {/* Right: Controls & Toggles */}
        <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
          {/* Rate & Volume metrics */}
          <div className="hidden sm:flex items-center gap-3 border-r border-zinc-800 pr-3 text-[11px] text-zinc-400">
            <span className="flex items-center gap-1 text-emerald-300">
              <Zap className="h-3 w-3 text-emerald-400" />
              ~{txRate} tx/min
            </span>
            <span className="text-zinc-500">|</span>
            <span className="text-zinc-300">
              Vol: LKR {totalVolLkr.toLocaleString()}
            </span>
          </div>

          {/* Speed Selector */}
          <select
            value={pollIntervalMs}
            onChange={(e) => setPollIntervalMs(Number(e.target.value))}
            className="rounded border border-zinc-800 bg-zinc-900 px-2 py-1 text-[11px] text-emerald-300 focus:outline-none focus:border-emerald-500"
          >
            <option value={1500}>1.5s (Fast)</option>
            <option value={2500}>2.5s (Normal)</option>
            <option value={5000}>5.0s (Slow)</option>
          </select>

          {/* Audio Beep Toggle */}
          <button
            onClick={() => setSoundEnabled((v) => !v)}
            title={soundEnabled ? "Mute register beeps" : "Enable register beeps"}
            className={`flex items-center gap-1 rounded border px-2 py-1 text-[11px] transition-colors ${
              soundEnabled
                ? "border-emerald-500/50 bg-emerald-950/60 text-emerald-300"
                : "border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200"
            }`}
          >
            {soundEnabled ? <Volume2 className="h-3 w-3" /> : <VolumeX className="h-3 w-3" />}
            <span className="hidden md:inline">{soundEnabled ? "Audio On" : "Muted"}</span>
          </button>

          {/* Play/Pause */}
          <button
            onClick={() => setIsPlaying((v) => !v)}
            className={`flex items-center gap-1 rounded border px-2 py-1 text-[11px] transition-colors ${
              isPlaying
                ? "border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
                : "border-emerald-500/50 bg-emerald-950/60 text-emerald-300"
            }`}
          >
            {isPlaying ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
            <span>{isPlaying ? "Pause" : "Resume"}</span>
          </button>

          {/* Refresh manual */}
          <button
            onClick={fetchFeed}
            disabled={isLoading}
            className="rounded border border-zinc-800 bg-zinc-900 p-1 text-zinc-400 hover:text-emerald-400 transition-colors"
            title="Poll now"
          >
            <RefreshCw className={`h-3 w-3 ${isLoading ? "animate-spin text-emerald-400" : ""}`} />
          </button>

          {/* Clear stream view */}
          <button
            onClick={() => setTransactions([])}
            className="rounded border border-zinc-800 bg-zinc-900 p-1 text-zinc-400 hover:text-red-400 transition-colors"
            title="Clear display"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
      </div>

      {/* Notice Banner (Scenario induction alert / Silence warning) */}
      {scenarioNotice && (
        <div className="flex items-center gap-2 border-b border-amber-500/30 bg-amber-950/40 px-4 py-2 font-mono text-xs text-amber-300 animate-pulse">
          <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
          <span>{scenarioNotice}</span>
        </div>
      )}

      {/* Terminal Filter Toolbar */}
      <div className="flex items-center justify-between gap-3 border-b border-zinc-800/80 bg-zinc-950/60 px-4 py-1.5 font-mono text-[11px] text-zinc-400">
        <div className="flex items-center gap-2 flex-1 max-w-sm">
          <Search className="h-3 w-3 text-zinc-500" />
          <input
            type="text"
            placeholder="Filter by SKU, product, aisle, or register..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-transparent text-emerald-300 placeholder-zinc-600 focus:outline-none"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm("")}
              className="text-zinc-500 hover:text-zinc-300 text-[10px]"
            >
              Clear
            </button>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-zinc-500">
            Buffered: <strong className="text-emerald-400">{filtered.length}</strong> items
          </span>
          <button
            onClick={() => setAutoScroll((v) => !v)}
            className={`flex items-center gap-1 text-[10px] ${
              autoScroll ? "text-emerald-400" : "text-zinc-500"
            }`}
          >
            <ArrowDownCircle className="h-3 w-3" />
            <span>Auto-top: {autoScroll ? "ON" : "OFF"}</span>
          </button>
        </div>
      </div>

      {/* Terminal Body / Streaming Table */}
      <div
        ref={terminalBodyRef}
        className="h-80 overflow-y-auto bg-black p-2 font-mono text-xs text-emerald-400 scrollbar-thin scrollbar-thumb-zinc-800"
      >
        {filtered.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-zinc-600">
            <Radio className="h-6 w-6 animate-pulse text-zinc-700" />
            <p>Awaiting checkout scan events from retail registers…</p>
            <button
              onClick={fetchFeed}
              className="rounded border border-zinc-800 bg-zinc-900 px-3 py-1 text-[11px] text-zinc-400 hover:text-emerald-300"
            >
              Fetch live feed
            </button>
          </div>
        ) : (
          <table className="w-full border-collapse text-left text-[11px]">
            <thead className="sticky top-0 bg-black/90 text-zinc-500 border-b border-zinc-800/80">
              <tr>
                <th className="py-1 px-2 font-normal">TIME</th>
                <th className="py-1 px-2 font-normal">REG</th>
                <th className="py-1 px-2 font-normal">SKU ID</th>
                <th className="py-1 px-2 font-normal">PRODUCT NAME</th>
                <th className="py-1 px-2 font-normal">LOC</th>
                <th className="py-1 px-2 font-normal text-right">QTY</th>
                <th className="py-1 px-2 font-normal text-right">PRICE (LKR)</th>
                <th className="py-1 px-2 font-normal text-right">TOTAL (LKR)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-900/80">
              {filtered.map((tx, idx) => {
                const timeStr = tx.timestamp.includes("T")
                  ? tx.timestamp.split("T")[1].substring(0, 8)
                  : tx.timestamp;
                const isHighlight =
                  tx.sku_id === "s1" || tx.sku_name.toLowerCase().includes("munchee");
                const regNumber = `REG-${((Number(tx.id) % 4) + 1).toString().padStart(2, "0")}`;

                return (
                  <tr
                    key={`${tx.id}-${idx}`}
                    className={`transition-colors hover:bg-zinc-900/80 ${
                      isHighlight
                        ? "bg-amber-950/30 text-amber-300 font-semibold border-l-2 border-amber-500"
                        : idx === 0
                        ? "bg-emerald-950/20 text-emerald-300"
                        : "text-emerald-400/90"
                    }`}
                  >
                    <td className="py-1 px-2 text-zinc-400 whitespace-nowrap">
                      {timeStr}
                    </td>
                    <td className="py-1 px-2 text-cyan-400 whitespace-nowrap">
                      {regNumber}
                    </td>
                    <td className="py-1 px-2 text-violet-300 font-semibold whitespace-nowrap">
                      {tx.sku_id}
                    </td>
                    <td className="py-1 px-2 text-zinc-200 truncate max-w-[200px]" title={tx.sku_name}>
                      {tx.sku_name}
                      {isHighlight && (
                        <span className="ml-2 rounded bg-amber-500/20 px-1 py-0.2 text-[9px] text-amber-300">
                          MONITORED
                        </span>
                      )}
                    </td>
                    <td className="py-1 px-2 text-zinc-400 whitespace-nowrap">
                      {tx.aisle ? `Aisle ${tx.aisle} · ${tx.bay}` : "—"}
                    </td>
                    <td className="py-1 px-2 text-right text-emerald-300 whitespace-nowrap">
                      x{tx.quantity}
                    </td>
                    <td className="py-1 px-2 text-right text-zinc-400 whitespace-nowrap">
                      {tx.unit_price.toFixed(2)}
                    </td>
                    <td className="py-1 px-2 text-right font-medium text-emerald-300 whitespace-nowrap">
                      {tx.total_amount.toFixed(2)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Terminal Footer Telemetry Line */}
      <div className="flex items-center justify-between border-t border-emerald-500/20 bg-zinc-950 px-4 py-1.5 font-mono text-[10px] text-zinc-500">
        <span>VORTEX_SCOUT_POS_PROTOCOL v2.4 // READY</span>
        <span className="text-emerald-400">STATUS: 200 OK // FEED ONLINE</span>
      </div>
    </div>
  );
}
