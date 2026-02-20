"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-xl font-medium">Something went wrong</h1>
      <p className="text-sm text-[var(--muted-foreground)]">{error.message}</p>
      <button
        onClick={reset}
        className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm text-[var(--primary-foreground)]"
      >
        Try again
      </button>
    </main>
  );
}
