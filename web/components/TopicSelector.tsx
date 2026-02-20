"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";
import type { TopicData } from "@/lib/api";

interface TopicSelectorProps {
  topics: TopicData[];
  onSelect: (index: number) => void;
  disabled?: boolean;
}

export function TopicSelector({ topics, onSelect, disabled }: TopicSelectorProps) {
  const [selected, setSelected] = useState<number | null>(null);

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="grid gap-3 sm:grid-cols-2">
        {topics.map((topic, i) => (
          <button
            key={i}
            type="button"
            disabled={disabled}
            onClick={() => setSelected(i)}
            className={cn(
              "rounded-lg border p-4 text-left transition-all hover:shadow-md",
              selected === i
                ? "border-[var(--primary)] bg-[var(--accent)] shadow-sm"
                : "border-[var(--border)] hover:border-[var(--muted-foreground)]"
            )}
          >
            <h4 className="font-medium text-sm leading-snug mb-2">
              {topic.title}
            </h4>
            <p className="text-xs text-[var(--muted-foreground)] mb-2 line-clamp-2">
              {topic.hook}
            </p>
            <div className="flex flex-wrap gap-1">
              <span className="text-xs bg-[var(--muted)] rounded px-1.5 py-0.5">
                {topic.target_audience.slice(0, 40)}
                {topic.target_audience.length > 40 ? "..." : ""}
              </span>
            </div>
            {topic.estimated_sections.length > 0 && (
              <div className="mt-2 text-xs text-[var(--muted-foreground)]">
                {topic.estimated_sections.length} sections
              </div>
            )}
          </button>
        ))}
      </div>

      <button
        type="button"
        disabled={disabled || selected === null}
        onClick={() => selected !== null && onSelect(selected)}
        className="w-full rounded-lg bg-[var(--primary)] px-6 py-3 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Write Article
      </button>
    </div>
  );
}
