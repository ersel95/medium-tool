const API_BASE = "http://localhost:8000";

export interface AnalysisData {
  name: string;
  total_files: number;
  total_lines: number;
  primary_language: string | null;
  languages: Record<string, number>;
  project_types: string[];
  frameworks: string[];
  dependencies: string[];
  readme_preview: string;
}

export interface TopicData {
  title: string;
  hook: string;
  angle: string;
  target_audience: string;
  estimated_sections: string[];
}

export interface ImagePrompt {
  marker: string;
  description: string;
}

export interface ArticleData {
  id?: string;
  title: string;
  subtitle: string;
  markdown: string;
  tags: string[];
  image_prompts: ImagePrompt[];
}

export interface ArticleListItem {
  id: string;
  title: string;
  project_name: string;
  created_at: string;
  updated_at: string;
}

async function get<T>(endpoint: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${endpoint}`);
  if (!resp.ok) {
    const text = await resp.text();
    let detail = text;
    try { detail = JSON.parse(text).detail || text; } catch {}
    throw new Error(detail);
  }
  return resp.json();
}

async function put<T>(endpoint: string, body: Record<string, unknown>): Promise<T> {
  const resp = await fetch(`${API_BASE}${endpoint}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const text = await resp.text();
    let detail = text;
    try { detail = JSON.parse(text).detail || text; } catch {}
    throw new Error(detail);
  }
  return resp.json();
}

async function del<T>(endpoint: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${endpoint}`, { method: "DELETE" });
  if (!resp.ok) {
    const text = await resp.text();
    let detail = text;
    try { detail = JSON.parse(text).detail || text; } catch {}
    throw new Error(detail);
  }
  return resp.json();
}

async function post<T>(endpoint: string, body: Record<string, unknown>, timeoutMs = 300_000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const resp = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!resp.ok) {
      const text = await resp.text();
      let detail = text;
      try {
        detail = JSON.parse(text).detail || text;
      } catch {}
      throw new Error(detail);
    }

    return resp.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Request timed out. The AI model may be taking too long.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export function analyzeProject(data: {
  path: string;
}): Promise<{ session_id: string; analysis: AnalysisData }> {
  return post("/api/analyze", data);
}

export function generateTopics(data: {
  session_id: string;
  language: string;
  topic_count: number;
}): Promise<{ topics: TopicData[] }> {
  return post("/api/topics", data);
}

export function writeArticle(data: {
  session_id: string;
  topic_index: number;
  language: string;
}): Promise<{ article: ArticleData; article_id: string }> {
  return post("/api/write", data);
}

export function saveArticle(data: {
  markdown: string;
  output_path: string;
}): Promise<{ success: boolean; path?: string; error?: string }> {
  return post("/api/save", data);
}

// ── Article History ──────────────────────────────────

export function listArticles(): Promise<{ articles: ArticleListItem[] }> {
  return get("/api/articles");
}

export function getArticle(id: string): Promise<{ article: ArticleData & { id: string; project_name: string; created_at: string; updated_at: string } }> {
  return get(`/api/articles/${id}`);
}

export function updateArticle(id: string, data: Partial<ArticleData>): Promise<{ success: boolean }> {
  return put(`/api/articles/${id}`, data as Record<string, unknown>);
}

export function deleteArticle(id: string): Promise<{ success: boolean }> {
  return del(`/api/articles/${id}`);
}

// ── Title Suggestions ────────────────────────────────

export function suggestTitles(data: {
  markdown: string;
  language: string;
}): Promise<{ titles: string[] }> {
  return post("/api/titles", data);
}

// ── Article Revision ─────────────────────────────────

export function reviseArticle(data: {
  markdown: string;
  instruction: string;
  language: string;
}): Promise<{ markdown: string }> {
  return post("/api/revise", data);
}

// ── Social Media Posts ──────────────────────────────

export interface SocialPost {
  tone: string;
  text: string;
}

export interface SocialPosts {
  twitter?: SocialPost[];
  linkedin?: SocialPost[];
  hackernews?: SocialPost[];
}

export function generateSocialPosts(data: {
  title: string;
  subtitle: string;
  markdown: string;
  article_url: string;
  language: string;
}): Promise<{ posts: SocialPosts }> {
  return post("/api/social-posts", data);
}
