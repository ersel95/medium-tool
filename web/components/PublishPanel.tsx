"use client";

import { useState } from "react";
import type { ArticleData } from "@/lib/api";
import { saveArticle } from "@/lib/api";

interface PublishPanelProps {
  article: ArticleData;
  onNext?: () => void;
}

export function PublishPanel({ article, onNext }: PublishPanelProps) {
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [savePath, setSavePath] = useState("");

  const handleDownload = () => {
    const blob = new Blob([article.markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${article.title.replace(/[^a-zA-Z0-9]/g, "-").toLowerCase()}.md`;
    a.click();
    URL.revokeObjectURL(url);
    setStatus("Downloaded!");
  };

  const handleCopyMarkdown = () => {
    navigator.clipboard.writeText(article.markdown);
    setStatus("Copied to clipboard!");
  };

  const handleSaveToServer = async () => {
    if (!savePath.trim()) return;
    setLoading(true);
    setStatus("Saving...");
    const result = await saveArticle({
      markdown: article.markdown,
      output_path: savePath.trim(),
    });
    setLoading(false);
    if (result.success) {
      setStatus(`Saved to ${result.path}`);
    } else {
      setStatus(`Error: ${result.error}`);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Article summary */}
      <div className="rounded-lg border border-[var(--border)] p-5">
        <h3 className="font-semibold mb-1">{article.title}</h3>
        {article.subtitle && (
          <p className="text-sm text-[var(--muted-foreground)] mb-3">
            {article.subtitle}
          </p>
        )}
        <div className="flex flex-wrap gap-1.5">
          {article.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center rounded-full bg-[var(--muted)] px-2.5 py-0.5 text-xs"
            >
              {tag}
            </span>
          ))}
        </div>
        <p className="text-xs text-[var(--muted-foreground)] mt-3">
          {article.markdown.split(/\s+/).length} words
        </p>
      </div>

      {/* Export options */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium">Export</h4>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={handleDownload}
            disabled={loading}
            className="rounded-lg border border-[var(--border)] px-6 py-3 text-sm font-medium transition-colors hover:bg-[var(--muted)] disabled:opacity-50"
          >
            Download .md
          </button>
          <button
            type="button"
            onClick={handleCopyMarkdown}
            disabled={loading}
            className="rounded-lg border border-[var(--border)] px-6 py-3 text-sm font-medium transition-colors hover:bg-[var(--muted)] disabled:opacity-50"
          >
            Copy Markdown
          </button>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={savePath}
            onChange={(e) => setSavePath(e.target.value)}
            placeholder="/path/to/save/article.md"
            className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--background)] px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
          <button
            type="button"
            onClick={handleSaveToServer}
            disabled={loading || !savePath.trim()}
            className="rounded-lg border border-[var(--border)] px-4 py-3 text-sm font-medium transition-colors hover:bg-[var(--muted)] disabled:opacity-50"
          >
            Save
          </button>
        </div>
      </div>

      {/* Status */}
      {status && (
        <div
          className={`rounded-lg p-4 text-sm ${
            status.startsWith("Error")
              ? "bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300"
              : "bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-300"
          }`}
        >
          {status}
        </div>
      )}

      {/* Next: Share */}
      {onNext && (
        <button
          type="button"
          onClick={onNext}
          className="w-full rounded-lg bg-[var(--primary)] px-6 py-3 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90"
        >
          Continue to Share
        </button>
      )}
    </div>
  );
}
