"use client";

import { useCallback, useEffect, useState } from "react";
import { StepWizard } from "@/components/StepWizard";
import { ProjectInput } from "@/components/ProjectInput";
import { AnalysisView } from "@/components/AnalysisView";
import { TopicSelector } from "@/components/TopicSelector";
import { ArticleEditor } from "@/components/ArticleEditor";
import { PublishPanel } from "@/components/PublishPanel";
import { SharePanel } from "@/components/SharePanel";
import { LoadingStep } from "@/components/LoadingStep";
import { ArticleHistory } from "@/components/ArticleHistory";
import {
  analyzeProject,
  generateTopics,
  writeArticle,
  listArticles,
  getArticle,
  deleteArticle,
  updateArticle,
} from "@/lib/api";
import type { AnalysisData, TopicData, ArticleData, ArticleListItem } from "@/lib/api";

const STEPS = [
  { label: "Project" },
  { label: "Topics" },
  { label: "Article" },
  { label: "Export" },
  { label: "Share" },
];

export default function Home() {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("");
  const [error, setError] = useState<string>("");

  // Data
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [topics, setTopics] = useState<TopicData[]>([]);
  const [sessionId, setSessionId] = useState<string>("");
  const [language, setLanguage] = useState<string>("en");
  const [article, setArticle] = useState<ArticleData | null>(null);
  const [articleId, setArticleId] = useState<string>("");

  // History
  const [history, setHistory] = useState<ArticleListItem[]>([]);

  const fetchHistory = useCallback(async () => {
    try {
      const result = await listArticles();
      setHistory(result.articles);
    } catch {
      // silently fail
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleAnalyze = useCallback(
    async (data: { path: string; language: string; topicCount: number }) => {
      setLoading(true);
      setError("");
      setLanguage(data.language);

      const isGitUrl = data.path.startsWith("http") || data.path.startsWith("git@");

      try {
        // Step 1: Analyze project (fast for local, slower for git clone)
        setLoadingMessage(isGitUrl ? "Cloning repository and analyzing..." : "Analyzing project...");
        const analyzeResult = await analyzeProject({ path: data.path });
        setAnalysis(analyzeResult.analysis);
        setSessionId(analyzeResult.session_id);

        // Step 2: Generate topics (slow - calls Claude)
        setLoadingMessage("Generating topic ideas (this may take a minute)...");
        const topicsResult = await generateTopics({
          session_id: analyzeResult.session_id,
          language: data.language,
          topic_count: data.topicCount,
        });
        setTopics(topicsResult.topics);
        setCurrentStep(1);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
        setLoadingMessage("");
      }
    },
    []
  );

  const handleTopicSelect = useCallback(
    async (topicIndex: number) => {
      setLoading(true);
      setError("");
      setLoadingMessage("Writing article (this may take a minute)...");

      try {
        const result = await writeArticle({
          session_id: sessionId,
          topic_index: topicIndex,
          language,
        });
        setArticle(result.article);
        setArticleId(result.article_id);
        setCurrentStep(2);
        fetchHistory();
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
        setLoadingMessage("");
      }
    },
    [sessionId, language, fetchHistory]
  );

  const handleArticleChange = useCallback(
    (updated: ArticleData) => {
      setArticle(updated);
      // Auto-save to DB if we have an article ID
      if (articleId) {
        updateArticle(articleId, {
          title: updated.title,
          subtitle: updated.subtitle,
          markdown: updated.markdown,
          tags: updated.tags,
          image_prompts: updated.image_prompts,
        }).catch(() => {});
      }
    },
    [articleId]
  );

  const handleGoToExport = useCallback(() => {
    setCurrentStep(3);
  }, []);

  const handleGoToShare = useCallback(() => {
    setCurrentStep(4);
  }, []);

  const handleStepClick = useCallback(
    (step: number) => {
      if (step < currentStep) {
        setCurrentStep(step);
      }
    },
    [currentStep]
  );

  const handleBackToTopics = useCallback(() => {
    setCurrentStep(1);
  }, []);

  const handleSelectHistory = useCallback(async (id: string) => {
    setLoading(true);
    setError("");
    setLoadingMessage("Loading article...");
    try {
      const result = await getArticle(id);
      const a = result.article;
      setArticle({
        title: a.title,
        subtitle: a.subtitle,
        markdown: a.markdown,
        tags: a.tags,
        image_prompts: a.image_prompts,
      });
      setArticleId(id);
      setCurrentStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
      setLoadingMessage("");
    }
  }, []);

  const handleDeleteHistory = useCallback(
    async (id: string) => {
      try {
        await deleteArticle(id);
        fetchHistory();
      } catch {
        // silently fail
      }
    },
    [fetchHistory]
  );

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:py-12">
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          Medium Tool
        </h1>
        <p className="text-sm text-[var(--muted-foreground)] mt-1">
          Analyze code projects and generate Medium articles with AI
        </p>
      </header>

      <StepWizard
        steps={STEPS}
        currentStep={currentStep}
        loadingMessage={loading ? loadingMessage : undefined}
        onStepClick={handleStepClick}
      />

      {error && (
        <div className="mb-6 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {error}
          <button
            type="button"
            onClick={() => setError("")}
            className="ml-2 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Step 0: Project Input */}
      {currentStep === 0 && !loading && (
        <div className="space-y-6">
          <ProjectInput onSubmit={handleAnalyze} />
          <ArticleHistory
            articles={history}
            onSelect={handleSelectHistory}
            onDelete={handleDeleteHistory}
          />
        </div>
      )}

      {/* Step 0: Loading */}
      {currentStep === 0 && loading && (
        <LoadingStep message={loadingMessage} />
      )}

      {/* Step 1: Topic Selection */}
      {currentStep === 1 && !loading && (
        <div className="space-y-6">
          {analysis && <AnalysisView analysis={analysis} />}
          <TopicSelector topics={topics} onSelect={handleTopicSelect} />
        </div>
      )}

      {/* Step 1: Loading (writing article) */}
      {currentStep === 1 && loading && (
        <LoadingStep message={loadingMessage} />
      )}

      {/* Step 2: Article Editor */}
      {currentStep === 2 && article && (
        <ArticleEditor
          article={article}
          language={language}
          onChange={handleArticleChange}
          onNext={handleGoToExport}
          onBack={topics.length > 0 ? handleBackToTopics : undefined}
        />
      )}

      {/* Step 3: Export */}
      {currentStep === 3 && article && (
        <PublishPanel article={article} onNext={handleGoToShare} />
      )}

      {/* Step 4: Share */}
      {currentStep === 4 && article && (
        <SharePanel article={article} language={language} />
      )}
    </main>
  );
}
