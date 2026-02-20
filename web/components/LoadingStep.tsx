"use client";

import { Loader2 } from "lucide-react";

interface LoadingStepProps {
  message: string;
}

export function LoadingStep({ message }: LoadingStepProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 animate-fade-in">
      <Loader2 className="h-8 w-8 animate-spin text-[var(--muted-foreground)] mb-4" />
      <p className="text-sm text-[var(--muted-foreground)]">{message}</p>
    </div>
  );
}
