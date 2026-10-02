import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Scout — Shelf-void intelligence",
  description:
    "Autonomous shelf-void detection & micro-audit intelligence for modern retail.",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#E11D48",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
