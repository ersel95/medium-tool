"use client";

import { useState, useRef, useEffect } from "react";
import dynamic from "next/dynamic";
import { Copy, Check, Sparkles, Send, Loader2 } from "lucide-react";
import type { ArticleData } from "@/lib/api";
import { suggestTitles, reviseArticle } from "@/lib/api";

const MDEditor = dynamic(() => import("@uiw/react-md-editor"), { ssr: false });

interface ArticleEditorProps {
  article: ArticleData;
  language: string;
  onChange: (article: ArticleData) => void;
  onNext: () => void;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function ArticleEditor({ article, language, onChange, onNext }: ArticleEditorProps) {
  const [activeTab, setActiveTab] = useState<"edit" | "preview">("edit");
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  // Title suggestions
  const [titleLoading, setTitleLoading] = useState(false);
  const [titleSuggestions, setTitleSuggestions] = useState<string[]>([]);
  const [showTitleDropdown, setShowTitleDropdown] = useState(false);

  // Chat revision
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [revising, setRevising] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const updateField = <K extends keyof ArticleData>(
    field: K,
    value: ArticleData[K]
  ) => {
    onChange({ ...article, [field]: value });
  };

  const copyPrompt = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const handleSuggestTitles = async () => {
    setTitleLoading(true);
    try {
      const result = await suggestTitles({ markdown: article.markdown, language });
      setTitleSuggestions(result.titles);
      setShowTitleDropdown(true);
    } catch {
      // silently fail
    } finally {
      setTitleLoading(false);
    }
  };

  const handleSelectTitle = (title: string) => {
    updateField("title", title);
    setShowTitleDropdown(false);
  };

  const handleRevise = async () => {
    const instruction = chatInput.trim();
    if (!instruction || revising) return;

    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", content: instruction }]);
    setRevising(true);

    try {
      const result = await reviseArticle({
        markdown: article.markdown,
        instruction,
        language,
      });
      onChange({ ...article, markdown: result.markdown });
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Article updated." },
      ]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err instanceof Error ? err.message : String(err)}` },
      ]);
    } finally {
      setRevising(false);
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Metadata Bar */}
      <div className="space-y-3 rounded-lg border border-[var(--border)] p-4">
        <div>
          <label className="block text-xs text-[var(--muted-foreground)] mb-1">
            Title
          </label>
          <div className="relative">
            <div className="flex gap-2">
              <input
                type="text"
                value={article.title}
                onChange={(e) => updateField("title", e.target.value)}
                className="flex-1 rounded border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
              />
              <button
                type="button"
                onClick={handleSuggestTitles}
                disabled={titleLoading}
                className="shrink-0 flex items-center gap-1.5 rounded border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-xs font-medium hover:bg-[var(--muted)] transition-colors disabled:opacity-50"
                title="Suggest titles"
              >
                {titleLoading ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Sparkles className="h-3.5 w-3.5" />
                )}
                Suggest
              </button>
            </div>
            {showTitleDropdown && titleSuggestions.length > 0 && (
              <div className="absolute z-10 mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--background)] shadow-lg">
                {titleSuggestions.map((t, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => handleSelectTitle(t)}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-[var(--muted)] transition-colors first:rounded-t-lg last:rounded-b-lg"
                  >
                    {t}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => setShowTitleDropdown(false)}
                  className="w-full text-left px-3 py-1.5 text-xs text-[var(--muted-foreground)] hover:bg-[var(--muted)] rounded-b-lg border-t border-[var(--border)]"
                >
                  Dismiss
                </button>
              </div>
            )}
          </div>
        </div>
        <div>
          <label className="block text-xs text-[var(--muted-foreground)] mb-1">
            Subtitle
          </label>
          <input
            type="text"
            value={article.subtitle}
            onChange={(e) => updateField("subtitle", e.target.value)}
            className="w-full rounded border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
        </div>
        <div>
          <label className="block text-xs text-[var(--muted-foreground)] mb-1">
            Tags (comma-separated)
          </label>
          <input
            type="text"
            value={article.tags.join(", ")}
            onChange={(e) =>
              updateField(
                "tags",
                e.target.value.split(",").map((t) => t.trim()).filter(Boolean)
              )
            }
            className="w-full rounded border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
        </div>
      </div>

      {/* Image Prompts */}
      {article.image_prompts.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30 p-4">
          <h4 className="text-sm font-medium mb-3">
            Image Prompts ({article.image_prompts.length})
          </h4>
          <p className="text-xs text-[var(--muted-foreground)] mb-3">
            Makalede <code className="bg-[var(--muted)] px-1 rounded">[IMAGE: ...]</code> placeholder&apos;lar var.
            Asagidaki prompt&apos;lari kullanarak resimleri uretip, placeholder&apos;larin yerine ekleyebilirsin.
          </p>
          <div className="space-y-2">
            {article.image_prompts.map((prompt, i) => (
              <div
                key={i}
                className="flex items-start gap-2 rounded border border-amber-200 dark:border-amber-800 bg-white dark:bg-[var(--background)] p-3"
              >
                <span className="shrink-0 text-xs font-mono text-[var(--muted-foreground)] mt-0.5">
                  #{i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-mono text-[var(--muted-foreground)] mb-1 truncate">
                    {prompt.marker}
                  </p>
                  <p className="text-sm">{prompt.description}</p>
                </div>
                <button
                  type="button"
                  onClick={() => copyPrompt(prompt.description, i)}
                  className="shrink-0 rounded p-1.5 hover:bg-[var(--muted)] transition-colors"
                  title="Copy prompt"
                >
                  {copiedIdx === i ? (
                    <Check className="h-4 w-4 text-[var(--success)]" />
                  ) : (
                    <Copy className="h-4 w-4 text-[var(--muted-foreground)]" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab bar for mobile, split-pane for desktop */}
      <div className="sm:hidden flex rounded-lg border border-[var(--border)] overflow-hidden mb-2">
        {(["edit", "preview"] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                : "bg-[var(--background)]"
            }`}
          >
            {tab === "edit" ? "Edit" : "Preview"}
          </button>
        ))}
      </div>

      {/* Editor */}
      <div data-color-mode="auto">
        <div className="sm:hidden">
          {activeTab === "edit" ? (
            <MDEditor
              value={article.markdown}
              onChange={(val) => updateField("markdown", val || "")}
              height={500}
              preview="edit"
            />
          ) : (
            <MDEditor
              value={article.markdown}
              height={500}
              preview="preview"
              hideToolbar
            />
          )}
        </div>
        <div className="hidden sm:block">
          <MDEditor
            value={article.markdown}
            onChange={(val) => updateField("markdown", val || "")}
            height={600}
            preview="live"
          />
        </div>
      </div>

      {/* Chat Revision Panel */}
      <div className="rounded-lg border border-[var(--border)] overflow-hidden">
        <div className="px-4 py-2 bg-[var(--muted)] border-b border-[var(--border)]">
          <h4 className="text-xs font-medium text-[var(--muted-foreground)]">
            Revise with AI
          </h4>
        </div>
        {chatMessages.length > 0 && (
          <div className="max-h-48 overflow-y-auto p-3 space-y-2">
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`text-sm px-3 py-2 rounded-lg max-w-[85%] ${
                  msg.role === "user"
                    ? "ml-auto bg-[var(--primary)] text-[var(--primary-foreground)]"
                    : "bg-[var(--muted)]"
                }`}
              >
                {msg.content}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
        )}
        <div className="flex gap-2 p-3 border-t border-[var(--border)]">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleRevise()}
            placeholder="e.g. Make the intro more engaging..."
            disabled={revising}
            className="flex-1 rounded border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)] disabled:opacity-50"
          />
          <button
            type="button"
            onClick={handleRevise}
            disabled={revising || !chatInput.trim()}
            className="shrink-0 flex items-center gap-1.5 rounded bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {revising ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            Revise
          </button>
        </div>
      </div>

      {/* Next button */}
      <button
        type="button"
        onClick={onNext}
        className="w-full rounded-lg bg-[var(--primary)] px-6 py-3 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90"
      >
        Continue to Publish
      </button>
    </div>
  );
}
