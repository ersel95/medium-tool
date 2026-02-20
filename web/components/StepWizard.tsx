"use client";

import { cn } from "@/lib/cn";
import { Check, Loader2 } from "lucide-react";

export interface Step {
  label: string;
  description?: string;
}

interface StepWizardProps {
  steps: Step[];
  currentStep: number;
  loadingMessage?: string;
}

export function StepWizard({ steps, currentStep, loadingMessage }: StepWizardProps) {
  return (
    <nav className="mb-8">
      <ol className="flex items-center gap-2">
        {steps.map((step, i) => {
          const isCompleted = i < currentStep;
          const isCurrent = i === currentStep;

          return (
            <li key={i} className="flex items-center gap-2">
              {i > 0 && (
                <div
                  className={cn(
                    "h-px w-8 sm:w-12",
                    isCompleted ? "bg-[var(--success)]" : "bg-[var(--border)]"
                  )}
                />
              )}
              <div className="flex items-center gap-2">
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors",
                    isCompleted && "bg-[var(--success)] text-white",
                    isCurrent && "bg-[var(--primary)] text-[var(--primary-foreground)]",
                    !isCompleted && !isCurrent && "bg-[var(--muted)] text-[var(--muted-foreground)]"
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-4 w-4" />
                  ) : isCurrent ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    i + 1
                  )}
                </div>
                <span
                  className={cn(
                    "hidden text-sm sm:inline",
                    isCurrent && "font-medium",
                    !isCompleted && !isCurrent && "text-[var(--muted-foreground)]"
                  )}
                >
                  {step.label}
                </span>
              </div>
            </li>
          );
        })}
      </ol>
      {loadingMessage && (
        <p className="mt-3 text-sm text-[var(--muted-foreground)] animate-pulse">
          {loadingMessage}
        </p>
      )}
    </nav>
  );
}
