import { cn } from "@/lib/utils";

const tones = {
  alert: "bg-scout-alertBg text-scout-alert",
  success: "bg-scout-successBg text-emerald-700",
  warning: "bg-amber-100 text-amber-700",
  ai: "bg-scout-aiBg text-scout-ai",
  neutral: "bg-zinc-100 text-scout-muted",
};

export function Badge({
  tone = "neutral",
  className,
  children,
}: {
  tone?: keyof typeof tones;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium", tones[tone], className)}>
      {children}
    </span>
  );
}
