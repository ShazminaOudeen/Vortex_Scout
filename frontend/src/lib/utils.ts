import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const formatLKR = (n: number) =>
  `LKR ${n.toLocaleString("en-LK", { maximumFractionDigits: 0 })}`;
