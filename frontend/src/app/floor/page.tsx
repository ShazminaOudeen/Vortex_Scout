"use client";
import { useEffect, useState, useMemo, useCallback } from "react";
import { useSWRConfig } from "swr";
import {
  Sparkles,
  WifiOff,
  Download,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { AisleGroup } from "@/components/floor/AisleGroup";
import { QuickStatsBar } from "@/components/floor/QuickStatsBar";
import { ItemDetailSheet } from "@/components/floor/ItemDetailSheet";
import { AssociateModal } from "@/components/floor/AssociateModal";
import { UndoToast } from "@/components/floor/UndoToast";
import { AllClearScreen } from "@/components/floor/AllClearScreen";
import { ConfettiCanvas } from "@/components/floor/ConfettiCanvas";
import { useChecklist } from "@/hooks/useAnomalies";
import { api } from "@/lib/api";
import {
  playChime,
  triggerHaptic,
  isSoundEnabled,
  toggleSound,
} from "@/lib/feedback";
import {
  flushOfflineQueue,
  queueOfflineReconcile,
} from "@/lib/offlineQueue";
import type { Anomaly, AuditAction } from "@/lib/types";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const RESOLVED_STORAGE_KEY = "scout_floor_resolved_records";
const ASSOCIATE_STORAGE_KEY = "scout_associate_name";

export default function FloorPage() {
  const { data, error, isLoading, mutate: revalidateChecklist } = useChecklist();
  const { mutate } = useSWRConfig();

  // Local state that survives page refresh (Feature D1)
  const [resolvedIds, setResolvedIds] = useState<Set<string>>(new Set());
  const [isClientLoaded, setIsClientLoaded] = useState(false);

  // Associate identity (Feature D5)
  const [associateName, setAssociateName] = useState("Nimal Fernando");
  const [isAssociateModalOpen, setIsAssociateModalOpen] = useState(false);

  // Item detail sheet (Feature D4)
  const [selectedItem, setSelectedItem] = useState<Anomaly | null>(null);

  // Undo stack (Feature D5)
  const [lastAction, setLastAction] = useState<{
    anomaly: Anomaly;
    action: AuditAction;
  } | null>(null);

  // Audio & Haptics state (Feature D2)
  const [soundActive, setSoundActive] = useState(true);

  // PWA & Offline State (Feature D3)
  const [isOnline, setIsOnline] = useState(true);
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);

  // Confetti trigger (Feature D2)
  const [showConfetti, setShowConfetti] = useState(false);

  // Load persisted resolved items and associate from localStorage on mount
  useEffect(() => {
    setIsClientLoaded(true);
    setSoundActive(isSoundEnabled());

    try {
      const savedAssociate = localStorage.getItem(ASSOCIATE_STORAGE_KEY);
      if (savedAssociate) setAssociateName(savedAssociate);

      const savedResolved = localStorage.getItem(RESOLVED_STORAGE_KEY);
      if (savedResolved) {
        const parsed = JSON.parse(savedResolved);
        if (Array.isArray(parsed)) {
          setResolvedIds(new Set(parsed));
        }
      }
    } catch {
      // Ignore localStorage errors
    }

    // Register Service Worker for PWA (Feature D3)
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js")
        .then(() => console.log("Scout Service Worker registered"))
        .catch(() => {});
    }

    // Connectivity listeners
    const handleOnline = () => {
      setIsOnline(true);
      flushOfflineQueue().then((count) => {
        if (count > 0) revalidateChecklist();
      });
    };
    const handleOffline = () => setIsOnline(false);

    setIsOnline(navigator.onLine);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    // PWA Install prompt listener
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", handleBeforeInstall);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
    };
  }, [revalidateChecklist]);

  // Persist resolved items to localStorage whenever updated
  const updateResolved = useCallback((updater: (prev: Set<string>) => Set<string>) => {
    setResolvedIds((prev) => {
      const next = updater(prev);
      try {
        localStorage.setItem(
          RESOLVED_STORAGE_KEY,
          JSON.stringify(Array.from(next))
        );
      } catch {}
      return next;
    });
  }, []);

  // Compute total items and active un-resolved items
  const allItems = useMemo(() => {
    if (!data?.groups) return [];
    return data.groups.flatMap((g) => g.items);
  }, [data]);

  const total = allItems.length;

  const activeGroups = useMemo(() => {
    if (!data?.groups) return [];
    return data.groups.map((g) => ({
      ...g,
      items: g.items.filter((item) => !resolvedIds.has(item.id)),
    }));
  }, [data, resolvedIds]);

  const activeCount = useMemo(() => {
    return activeGroups.reduce((acc, g) => acc + g.items.length, 0);
  }, [activeGroups]);

  const verifiedCount = Math.min(total, total - activeCount);

  // Total revenue at risk
  const totalRevenueAtRisk = useMemo(() => {
    return activeGroups.reduce(
      (sum, g) =>
        sum +
        g.items.reduce((s, i) => s + (i.revenue_at_risk || 0), 0),
      0
    );
  }, [activeGroups]);

  // Handle audit reconcile action
  const handleAction = async (id: string, action: AuditAction) => {
    const target = allItems.find((i) => i.id === id);
    if (!target) return;

    // Trigger haptic & sound feedback (Feature D2)
    triggerHaptic("tap");
    playChime(action);

    // Update local resolved state immediately
    const nextResolvedCount = verifiedCount + 1;
    updateResolved((s) => new Set(s).add(id));

    // Save for undo (Feature D5)
    setLastAction({ anomaly: target, action });

    // Check if this was the last item -> Trigger completion moment (Feature D2)
    if (nextResolvedCount === total && total > 0) {
      setTimeout(() => {
        triggerHaptic("success");
        playChime("complete");
        setShowConfetti(true);
      }, 200);
    }

    // Call backend API with associate name (Feature D1 & D5)
    const payload = {
      anomaly_id: id,
      action,
      associate: associateName,
    };

    try {
      if (navigator.onLine) {
        await api.reconcile(payload);
        mutate("checklist");
      } else {
        queueOfflineReconcile(payload);
      }
    } catch {
      // In case of network fault, queue for later sync
      queueOfflineReconcile(payload);
    }
  };

  // Handle undo action (Feature D5)
  const handleUndo = async () => {
    if (!lastAction) return;
    const { anomaly } = lastAction;

    triggerHaptic("tap");
    playChime("undo");

    // Remove from resolved state
    updateResolved((s) => {
      const next = new Set(s);
      next.delete(anomaly.id);
      return next;
    });

    setLastAction(null);

    // Call backend undo endpoint
    try {
      if (navigator.onLine) {
        await api.undoReconcile({
          anomaly_id: anomaly.id,
          associate: associateName,
        });
        mutate("checklist");
      }
    } catch {
      // Local state is already restored
    }
  };

  // Save new associate name
  const handleSaveAssociate = (name: string) => {
    setAssociateName(name);
    try {
      localStorage.setItem(ASSOCIATE_STORAGE_KEY, name);
    } catch {}
  };

  // Toggle audio
  const handleToggleSound = () => {
    const next = toggleSound();
    setSoundActive(next);
  };

  // Reset session for demo replay
  const handleResetSession = () => {
    updateResolved(() => new Set());
    localStorage.removeItem(RESOLVED_STORAGE_KEY);
    revalidateChecklist();
  };

  // PWA Install prompt trigger
  const handleInstallClick = () => {
    if (installPrompt) {
      installPrompt.prompt();
      installPrompt.userChoice.then(() => setInstallPrompt(null));
    }
  };

  // Loading skeleton state (Feature D1)
  if (isLoading || !isClientLoaded) {
    return (
      <main className="mx-auto max-w-[440px] space-y-4 p-4 min-h-screen">
        <div className="h-28 rounded-2xl bg-zinc-200/70 animate-pulse" />
        <div className="h-16 rounded-xl bg-purple-100/50 animate-pulse" />
        <div className="space-y-3">
          <div className="h-4 w-32 rounded bg-zinc-200 animate-pulse" />
          <div className="h-32 rounded-2xl bg-zinc-200/60 animate-pulse" />
          <div className="h-32 rounded-2xl bg-zinc-200/60 animate-pulse" />
        </div>
      </main>
    );
  }

  // Error state (Feature D1)
  if (error && !data) {
    return (
      <main className="mx-auto max-w-[440px] space-y-4 p-6 min-h-screen flex flex-col items-center justify-center text-center">
        <div className="h-12 w-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mb-2">
          <AlertCircle className="h-6 w-6" />
        </div>
        <h2 className="text-lg font-bold text-zinc-900">Failed to load checklist</h2>
        <p className="text-sm text-scout-muted max-w-xs">
          Could not connect to Scout backend. Check network or local dev server.
        </p>
        <button
          onClick={() => revalidateChecklist()}
          className="mt-3 inline-flex items-center gap-2 rounded-xl bg-zinc-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-zinc-800"
        >
          <RefreshCw className="h-4 w-4" />
          Retry Connection
        </button>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-[440px] space-y-4 p-4 pb-20 min-h-screen">
      {/* Confetti celebration moment (Feature D2) */}
      {showConfetti && <ConfettiCanvas onComplete={() => setShowConfetti(false)} />}

      {/* Offline Alert Banner (Feature D3) */}
      {!isOnline && (
        <div className="flex items-center gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-semibold text-amber-700 animate-in fade-in">
          <WifiOff className="h-4 w-4 shrink-0 text-amber-600" />
          <span>Offline mode — actions are queued locally and will sync when reconnected.</span>
        </div>
      )}

      {/* PWA Install Banner if installable (Feature D3) */}
      {installPrompt && (
        <div className="flex items-center justify-between rounded-xl border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-700 animate-in fade-in">
          <div className="flex items-center gap-1.5">
            <Download className="h-4 w-4" />
            <span>Install Scout Floor App on phone</span>
          </div>
          <button
            onClick={handleInstallClick}
            className="rounded-lg bg-rose-600 px-2.5 py-1 text-[11px] font-bold text-white shadow-sm hover:bg-rose-700"
          >
            Install
          </button>
        </div>
      )}

      {/* Top Quick Stats Bar (Feature D2) */}
      <QuickStatsBar
        done={verifiedCount}
        total={total}
        minutes={data?.estimated_minutes ?? 3}
        totalRevenueAtRisk={totalRevenueAtRisk}
        associateName={associateName}
        onOpenAssociate={() => setIsAssociateModalOpen(true)}
        soundEnabled={soundActive}
        onToggleSound={handleToggleSound}
      />

      {/* Gemini AI Morning Briefing Card */}
      {data?.briefing && (
        <div className="rounded-2xl border border-purple-500/20 bg-gradient-to-r from-purple-50 via-white to-purple-50/40 p-3.5 text-xs text-purple-950 shadow-sm dark:bg-purple-950/20 dark:text-purple-200">
          <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[11px] text-purple-700 mb-1">
            <Sparkles className="h-3.5 w-3.5 text-purple-600" />
            <span>Scout AI Floor Briefing</span>
          </div>
          <p className="leading-relaxed text-zinc-700">{data.briefing}</p>
        </div>
      )}

      {/* Aisle Groups or All-Clear Screen */}
      {activeCount > 0 ? (
        activeGroups.map((g) => (
          <AisleGroup
            key={g.aisle}
            group={g}
            onAction={handleAction}
            onSelect={(item) => setSelectedItem(item)}
          />
        ))
      ) : (
        <AllClearScreen
          totalResolved={verifiedCount}
          totalRevenue={allItems.reduce((s, i) => s + (i.revenue_at_risk || 0), 0)}
          onRefresh={() => revalidateChecklist()}
          onResetSession={handleResetSession}
        />
      )}

      {/* Item Detail Sheet Modal (Feature D4) */}
      <ItemDetailSheet
        item={selectedItem}
        onClose={() => setSelectedItem(null)}
        onAction={handleAction}
      />

      {/* Associate Identity Switcher Modal (Feature D5) */}
      <AssociateModal
        current={associateName}
        isOpen={isAssociateModalOpen}
        onClose={() => setIsAssociateModalOpen(false)}
        onSave={handleSaveAssociate}
      />

      {/* Floating Undo Toast (Feature D5) */}
      {lastAction && (
        <UndoToast
          skuName={lastAction.anomaly.sku_name}
          action={lastAction.action}
          onUndo={handleUndo}
          onDismiss={() => setLastAction(null)}
        />
      )}
    </main>
  );
}
