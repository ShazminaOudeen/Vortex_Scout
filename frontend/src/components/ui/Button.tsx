import { cn } from "@/lib/utils";

const variants = {
  primary: "bg-scout-alert text-white hover:bg-rose-700",
  success: "bg-scout-success text-white hover:bg-emerald-600",
  warning: "bg-scout-warning text-white hover:bg-amber-600",
  ghost: "bg-zinc-100 text-scout-foreground hover:bg-zinc-200",
};

export function Button({
  variant = "primary",
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof variants;
}) {
  return (
    <button
      className={cn(
        "rounded-lg px-4 py-2.5 text-sm font-semibold transition disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
