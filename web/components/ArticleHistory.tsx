"use client";

import { Trash2 } from "lucide-react";
import type { ArticleListItem } from "@/lib/api";

interface ArticleHistoryProps {
  articles: ArticleListItem[];
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export function ArticleHistory({ articles, onSelect, onDelete }: ArticleHistoryProps) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-[var(--muted-foreground)]">
        Recent Articles
      </h3>
      {articles.length === 0 ? (
        <div className="rounded-lg border border-dashed border-[var(--border)] p-6 text-center">
          <p className="text-sm text-[var(--muted-foreground)]">
            No articles yet. Generate your first article above!
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {articles.map((a) => (
            <div
              key={a.id}
              className="group flex items-center gap-3 rounded-lg border border-[var(--border)] p-3 hover:bg-[var(--muted)] transition-colors cursor-pointer"
              onClick={() => onSelect(a.id)}
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {a.title || "Untitled"}
                </p>
                <p className="text-xs text-[var(--muted-foreground)] mt-0.5">
                  {a.project_name && <span>{a.project_name} &middot; </span>}
                  {new Date(a.updated_at).toLocaleDateString()}
                </p>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(a.id);
                }}
                className="shrink-0 rounded p-1.5 opacity-0 group-hover:opacity-100 hover:bg-red-100 dark:hover:bg-red-900/30 transition-all"
                title="Delete article"
              >
                <Trash2 className="h-4 w-4 text-red-500" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
