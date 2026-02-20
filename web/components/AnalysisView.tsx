"use client";

import type { AnalysisData } from "@/lib/api";

interface AnalysisViewProps {
  analysis: AnalysisData;
}

export function AnalysisView({ analysis }: AnalysisViewProps) {
  const topLangs = Object.entries(analysis.languages).slice(0, 5);

  return (
    <div className="rounded-lg border border-[var(--border)] p-5 animate-fade-in">
      <h3 className="text-lg font-semibold mb-3">{analysis.name}</h3>
      <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <Stat label="Files" value={analysis.total_files.toLocaleString()} />
        <Stat label="Lines" value={analysis.total_lines.toLocaleString()} />
        <Stat label="Language" value={analysis.primary_language || "Unknown"} />
        <Stat
          label="Type"
          value={analysis.project_types[0] || "Unknown"}
        />
      </div>

      {topLangs.length > 1 && (
        <div className="mt-4">
          <p className="text-xs text-[var(--muted-foreground)] mb-2">Language breakdown</p>
          <div className="flex flex-wrap gap-1.5">
            {topLangs.map(([lang, count]) => (
              <span
                key={lang}
                className="inline-flex items-center rounded-full bg-[var(--muted)] px-2.5 py-0.5 text-xs"
              >
                {lang} ({count})
              </span>
            ))}
          </div>
        </div>
      )}

      {analysis.frameworks.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-[var(--muted-foreground)] mb-2">Frameworks</p>
          <div className="flex flex-wrap gap-1.5">
            {analysis.frameworks.map((fw) => (
              <span
                key={fw}
                className="inline-flex items-center rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 px-2.5 py-0.5 text-xs"
              >
                {fw}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-[var(--muted-foreground)]">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
