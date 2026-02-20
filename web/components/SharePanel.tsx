"use client";

import { useState } from "react";
import { Copy, Check, Loader2, Sparkles } from "lucide-react";
import type { ArticleData } from "@/lib/api";
import { generateSocialPosts } from "@/lib/api";
import type { SocialPosts } from "@/lib/api";

interface SharePanelProps {
  article: ArticleData;
  language: string;
}

const PLATFORM_LABELS: Record<string, string> = {
  twitter: "X (Twitter)",
  linkedin: "LinkedIn",
  hackernews: "Hacker News",
};

const TONE_LABELS: Record<string, string> = {
  professional: "Professional",
  casual: "Casual",
  provocative: "Provocative",
  storytelling: "Storytelling",
  technical: "Technical",
  default: "Default",
};

export function SharePanel({ article, language }: SharePanelProps) {
  const [articleUrl, setArticleUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [posts, setPosts] = useState<SocialPosts | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!articleUrl.trim()) return;
    setLoading(true);
    setError("");
    try {
      const result = await generateSocialPosts({
        title: article.title,
        subtitle: article.subtitle,
        markdown: article.markdown,
        article_url: articleUrl.trim(),
        language,
      });
      setPosts(result.posts);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* URL Input */}
      <div className="rounded-lg border border-[var(--border)] p-5 space-y-3">
        <h3 className="font-semibold">Share Your Article</h3>
        <p className="text-sm text-[var(--muted-foreground)]">
          Paste your published Medium article link to generate social media posts in different tones.
        </p>
        <div className="flex gap-2">
          <input
            type="url"
            value={articleUrl}
            onChange={(e) => setArticleUrl(e.target.value)}
            placeholder="https://medium.com/@you/your-article-slug"
            className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--background)] px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
            disabled={loading}
          />
          <button
            type="button"
            onClick={handleGenerate}
            disabled={loading || !articleUrl.trim()}
            className="shrink-0 flex items-center gap-2 rounded-lg bg-[var(--primary)] px-5 py-3 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            Generate
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Generated Posts */}
      {posts && (
        <div className="space-y-5">
          {Object.entries(posts).map(([platform, items]) => {
            if (!Array.isArray(items) || items.length === 0) return null;
            return (
              <div key={platform} className="space-y-3">
                <h4 className="text-sm font-semibold">
                  {PLATFORM_LABELS[platform] || platform}
                </h4>
                <div className="space-y-2">
                  {items.map((item, i) => {
                    const key = `${platform}-${i}`;
                    return (
                      <div
                        key={key}
                        className="group rounded-lg border border-[var(--border)] p-4"
                      >
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <span className="inline-flex items-center rounded-full bg-[var(--muted)] px-2.5 py-0.5 text-xs font-medium">
                            {TONE_LABELS[item.tone] || item.tone}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleCopy(item.text, key)}
                            className="shrink-0 rounded p-1.5 hover:bg-[var(--muted)] transition-colors"
                            title="Copy"
                          >
                            {copiedKey === key ? (
                              <Check className="h-4 w-4 text-[var(--success)]" />
                            ) : (
                              <Copy className="h-4 w-4 text-[var(--muted-foreground)]" />
                            )}
                          </button>
                        </div>
                        <p className="text-sm whitespace-pre-wrap">{item.text}</p>
                        {platform === "twitter" && (
                          <p className="text-xs text-[var(--muted-foreground)] mt-2">
                            {item.text.length}/280 characters
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
