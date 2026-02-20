import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Medium Tool",
  description: "Analyze code projects and generate Medium articles with AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
