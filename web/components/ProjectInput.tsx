"use client";

import { useState } from "react";

interface ProjectInputProps {
  onSubmit: (data: {
    path: string;
    language: string;
    topicCount: number;
  }) => void;
  disabled?: boolean;
}

export function ProjectInput({ onSubmit, disabled }: ProjectInputProps) {
  const [path, setPath] = useState("");
  const [language, setLanguage] = useState("en");
  const [topicCount, setTopicCount] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!path.trim()) return;
    onSubmit({ path: path.trim(), language, topicCount });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 animate-fade-in">
      {/* Project Path */}
      <div>
        <label className="block text-sm font-medium mb-2">Project Path or Git URL</label>
        <input
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="/path/to/your/project or https://github.com/user/repo"
          className="w-full rounded-lg border border-[var(--border)] bg-[var(--background)] px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          disabled={disabled}
        />
      </div>

      {/* Settings Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Language */}
        <div>
          <label className="block text-sm font-medium mb-2">Language</label>
          <div className="flex rounded-lg border border-[var(--border)] overflow-hidden">
            {["en", "tr"].map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => setLanguage(lang)}
                disabled={disabled}
                className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                  language === lang
                    ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                    : "bg-[var(--background)] text-[var(--foreground)] hover:bg-[var(--muted)]"
                }`}
              >
                {lang.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Topic Count */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Topics: {topicCount}
          </label>
          <input
            type="range"
            min={3}
            max={10}
            value={topicCount}
            onChange={(e) => setTopicCount(Number(e.target.value))}
            disabled={disabled}
            className="w-full accent-[var(--primary)] mt-2"
          />
        </div>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={disabled || !path.trim()}
        className="w-full rounded-lg bg-[var(--primary)] px-6 py-3 text-sm font-medium text-[var(--primary-foreground)] transition-opacity hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Analyze Project
      </button>
    </form>
  );
}
