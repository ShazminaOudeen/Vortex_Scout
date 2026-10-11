"use client";
import { useState } from "react";
import { User, Check, X } from "lucide-react";
import { Button } from "@/components/ui/Button";

const COMMON_ASSOCIATES = [
  "Nimal Fernando",
  "Priyani Kulatunga",
  "Kasun Dissanayake",
  "Aathika Mansoor",
  "Chathura Perera",
];

interface AssociateModalProps {
  current: string;
  isOpen: boolean;
  onClose: () => void;
  onSave: (name: string) => void;
}

export function AssociateModal({
  current,
  isOpen,
  onClose,
  onSave,
}: AssociateModalProps) {
  const [customName, setCustomName] = useState(current);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-sm rounded-2xl border border-scout-border bg-scout-surface p-5 shadow-2xl animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between pb-3 border-b border-scout-border">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 text-zinc-700">
              <User className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-semibold text-zinc-900">Floor Associate</h3>
              <p className="text-xs text-scout-muted">Audit actions will be logged under this name</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 space-y-2">
          <label className="text-xs font-semibold uppercase text-scout-muted tracking-wider">
            Quick Select
          </label>
          <div className="flex flex-wrap gap-1.5">
            {COMMON_ASSOCIATES.map((name) => {
              const isSelected = customName === name;
              return (
                <button
                  key={name}
                  onClick={() => {
                    setCustomName(name);
                    onSave(name);
                    onClose();
                  }}
                  className={`flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${
                    isSelected
                      ? "bg-zinc-900 text-white"
                      : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
                  }`}
                >
                  {name}
                  {isSelected && <Check className="h-3 w-3" />}
                </button>
              );
            })}
          </div>

          <div className="pt-3">
            <label className="text-xs font-semibold uppercase text-scout-muted tracking-wider">
              Or Custom Name
            </label>
            <input
              type="text"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder="e.g. Ruwan Silva"
              className="mt-1 w-full rounded-lg border border-scout-border bg-scout-bg px-3 py-2 text-sm text-zinc-900 focus:border-zinc-900 focus:outline-none"
            />
          </div>
        </div>

        <div className="mt-5 flex gap-2 justify-end">
          <Button variant="ghost" onClick={onClose} className="text-xs">
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={() => {
              if (customName.trim()) {
                onSave(customName.trim());
                onClose();
              }
            }}
            className="text-xs px-4"
          >
            Save Associate
          </Button>
        </div>
      </div>
    </div>
  );
}
