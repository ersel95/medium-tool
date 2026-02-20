# Medium Tool

Analyze any code project (local or GitHub repo) and generate publish-ready Medium articles with AI.

Medium Tool scans your codebase, understands its structure, and uses Claude to write story-driven technical articles — complete with title suggestions, image prompts, and a chat-based revision workflow.

## Features

- **Project Analysis** — Point to a local directory or paste a GitHub URL. The tool scans files, detects languages, frameworks, and dependencies automatically.
- **AI Topic Generation** — Claude generates multiple article angles based on your project's actual code and architecture.
- **Article Writing** — Full 1500-2500 word articles in a conversational, story-driven style. Medium-compatible Markdown formatting out of the box.
- **Title Suggestions** — Get 5 AI-generated title alternatives and pick the best one.
- **Chat Revision** — Revise your article through a chat interface. Ask for tone changes, section rewrites, or structural edits.
- **Article History** — All generated articles are saved to a local SQLite database. Reopen and edit any previous article.
- **Image Prompts** — AI-generated image descriptions ready to copy into DALL-E, Midjourney, or any image generator.
- **Medium Publishing** — Publish directly to Medium as a draft or public post (requires Medium API token).
- **Multi-language** — Generate articles in English or Turkish.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Claude Code CLI** — installed and authenticated ([installation guide](https://docs.anthropic.com/en/docs/claude-code))
- **Git** — required for analyzing GitHub repositories

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/ersel95/medium-tool.git
cd medium-tool
```

### 2. Install the Python backend

```bash
pip install -e .
```

### 3. Install the frontend

```bash
cd web
npm install
cd ..
```

### 4. (Optional) Configure API keys

Copy `.env.example` to `.env` and fill in the keys you need:

```bash
cp .env.example .env
```

| Key | Required | Purpose |
|-----|----------|---------|
| `MEDIUM_TOKEN` | For publishing | Publish articles directly to Medium |
| `OPENAI_API_KEY` | For images | Generate images with DALL-E |
| `UNSPLASH_ACCESS_KEY` | For images | Fetch stock photos from Unsplash |

> Note: Article generation uses Claude Code CLI, not an API key. Make sure `claude` is available in your PATH.

### 5. Start the servers

**Backend** (port 8000):

```bash
uvicorn medium_tool.api.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 300
```

**Frontend** (port 3000):

```bash
cd web
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. **Enter a project path or GitHub URL** — e.g. `/Users/you/projects/my-app` or `https://github.com/user/repo`
2. **Pick a language** (EN/TR) and number of topics
3. **Select a topic** from the AI-generated suggestions
4. **Edit the article** — use the Markdown editor, suggest new titles, or revise via chat
5. **Publish** to Medium or save as a local `.md` file

## Project Structure

```
medium-tool/
├── src/medium_tool/          # Python backend
│   ├── api/                  # FastAPI routes, SQLite database
│   ├── analyzer/             # Project scanning and analysis
│   ├── generator/            # Claude-powered writing, titles, revision
│   ├── images/               # DALL-E and Unsplash integration
│   └── publisher/            # Medium API client
├── web/                      # Next.js frontend
│   ├── app/                  # Pages
│   ├── components/           # UI components
│   └── lib/                  # API client
├── pyproject.toml
└── .env.example
```

## Tech Stack

- **Backend**: Python, FastAPI, SQLite, Claude Code CLI
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, MDEditor

## License

MIT
