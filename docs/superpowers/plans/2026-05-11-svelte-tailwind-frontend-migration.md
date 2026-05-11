# SvelteKit + Tailwind v4 Frontend Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Streamlit Python chat in `frontend/` with a SvelteKit + Tailwind v4 SPA, keeping feature parity (create conversation, send message, render history with chunk sources) and adding small UX wins (typing indicator, "new conversation" button, localStorage persistence, Markdown rendering).

**Architecture:** SvelteKit (Svelte 5 runes) built as a static SPA via `@sveltejs/adapter-static`, calling the existing FastAPI backend directly from the browser. A CORS middleware is added to FastAPI. Tailwind v4 (CSS-first config) drives styling with a Simplon brand palette. State is held in a single rune-based store; Markdown is rendered with `marked` + sanitized with `DOMPurify`.

**Tech Stack:** SvelteKit 2 / Svelte 5, TypeScript (strict), Tailwind CSS v4, Vite, Bun, marked + DOMPurify, Vitest + `@testing-library/svelte` + jsdom, ESLint + Prettier.

---

## File map

**Created**
- `frontend/.env.example`, `frontend/.gitignore`, `frontend/.prettierrc`, `frontend/.prettierignore`, `frontend/eslint.config.js`
- `frontend/package.json`, `frontend/svelte.config.js`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/vitest-setup.ts`
- `frontend/src/app.html`, `frontend/src/app.css`, `frontend/src/app.d.ts`
- `frontend/src/lib/types.ts`
- `frontend/src/lib/api/client.ts`, `frontend/src/lib/api/client.test.ts`
- `frontend/src/lib/stores/chat.svelte.ts`, `frontend/src/lib/stores/chat.test.ts`
- `frontend/src/lib/components/{ChatHeader,MessageList,MessageBubble,SourcesPanel,TypingIndicator,ChatInput}.svelte`
- `frontend/src/lib/components/MessageBubble.test.ts`, `frontend/src/lib/components/ChatInput.test.ts`
- `frontend/src/routes/+layout.svelte`, `frontend/src/routes/+layout.ts`, `frontend/src/routes/+page.svelte`
- `frontend/README.md` (new content)
- `.github/workflows/frontend.yml`

**Modified**
- `api/src/rag/api/app.py` — add CORS middleware
- `api/src/rag/config/settings.py` — add `cors_allowed_origins` setting
- `api/tests/integration/test_cors.py` — new CORS test (created)
- `.pre-commit-config.yaml` — frontend lint hook
- `.gitignore` — node_modules, .svelte-kit, build, .env
- `CLAUDE.md`, `docs/AGENTS.md`, `docs/TECHNICAL_GUIDE.md`, `docs/PROJECT_STRUCTURE.md`, `docs/FEATURES.md`, `docs/TASKS.md`, root `README.md`

**Deleted (Streamlit removal)**
- `frontend/src/app/`, `frontend/tests/`, `frontend/.streamlit/`, `frontend/pyproject.toml`, `frontend/uv.lock`, `frontend/.venv/`, `frontend/.pytest_cache/`

---

## Task 1: Add CORS middleware to FastAPI

**Files:**
- Modify: `api/src/rag/config/settings.py`
- Modify: `api/src/rag/api/app.py`
- Create: `api/tests/integration/test_cors.py`

- [ ] **Step 1: Write the failing test**

Create `api/tests/integration/test_cors.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_preflight_allows_sveltekit_dev_origin(async_client: AsyncClient):
    response = await async_client.options(
        "/api/v1/conversations",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


@pytest.mark.asyncio
async def test_cors_preflight_rejects_unknown_origin(async_client: AsyncClient):
    response = await async_client.options(
        "/api/v1/conversations",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    # Without a matching allow-origin header the browser will block the call.
    assert "access-control-allow-origin" not in {k.lower() for k in response.headers}
```

- [ ] **Step 2: Run test, confirm it fails**

Run: `cd api && uv run pytest tests/integration/test_cors.py -v`
Expected: both tests FAIL (no CORS middleware, OPTIONS returns 405 or no headers).

- [ ] **Step 3: Add CORS setting**

Edit `api/src/rag/config/settings.py`. Inside `class Settings`, add after `app_port`:

```python
    # CORS — comma-separated origins allowed to call the API from a browser.
    cors_allowed_origins: str = "http://localhost:5173,http://localhost:4173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]
```

- [ ] **Step 4: Add CORS middleware**

Edit `api/src/rag/api/app.py`. Replace the existing `create_app` body with:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag.api.routers import chat, eval, health, ingestion
from rag.config.settings import get_settings
from rag.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Simplon RAG Sample API",
        description="Sample RAG support chatbot API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
    )

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(ingestion.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(eval.router, prefix="/api/v1")

    return app
```

- [ ] **Step 5: Run tests, confirm they pass**

Run: `cd api && uv run pytest tests/integration/test_cors.py -v`
Expected: both tests PASS.

Run full API test suite to check no regression: `cd api && uv run pytest`
Expected: all tests PASS.

- [ ] **Step 6: Document the new env var**

Append to `.env.example` at repo root (or create if not present):

```env
# Comma-separated list of origins allowed to call the API from a browser.
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:4173
```

- [ ] **Step 7: Commit**

```bash
git add api/src/rag/config/settings.py api/src/rag/api/app.py api/tests/integration/test_cors.py .env.example
git commit -m "feat(api): Add CORS middleware for SvelteKit frontend"
```

---

## Task 2: Remove Streamlit frontend

**Files:**
- Delete: everything under `frontend/`

- [ ] **Step 1: Confirm the directory contents**

Run: `ls -A frontend/`
Expected output should mention `src`, `tests`, `pyproject.toml`, `uv.lock`, `.streamlit`, possibly `.venv` and `.pytest_cache`. No surprise files.

- [ ] **Step 2: Delete tracked Streamlit files**

```bash
git rm -r frontend/src frontend/tests frontend/.streamlit frontend/pyproject.toml frontend/uv.lock frontend/README.md
```

- [ ] **Step 3: Delete untracked artifacts**

```bash
rm -rf frontend/.venv frontend/.pytest_cache
```

- [ ] **Step 4: Confirm `frontend/` is empty**

Run: `ls -A frontend/`
Expected: empty (or only `.DS_Store` on macOS — leave it).

- [ ] **Step 5: Commit**

```bash
git commit -m "chore(frontend): Remove Streamlit frontend"
```

---

## Task 3: Bootstrap SvelteKit project (manifest, build config, lint)

**Files:**
- Create: `frontend/package.json`, `frontend/svelte.config.js`, `frontend/vite.config.ts`, `frontend/tsconfig.json`
- Create: `frontend/.gitignore`, `frontend/.prettierrc`, `frontend/.prettierignore`, `frontend/eslint.config.js`
- Create: `frontend/.env.example`

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "rag-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview",
    "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
    "lint": "prettier --check . && eslint .",
    "format": "prettier --write .",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "devDependencies": {
    "@sveltejs/adapter-static": "^3.0.6",
    "@sveltejs/kit": "^2.8.0",
    "@sveltejs/vite-plugin-svelte": "^4.0.0",
    "@tailwindcss/vite": "^4.0.0",
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/svelte": "^5.2.0",
    "@types/dompurify": "^3.0.5",
    "@types/marked": "^6.0.0",
    "eslint": "^9.14.0",
    "eslint-config-prettier": "^9.1.0",
    "eslint-plugin-svelte": "^2.46.0",
    "globals": "^15.12.0",
    "jsdom": "^25.0.1",
    "prettier": "^3.3.3",
    "prettier-plugin-svelte": "^3.2.7",
    "svelte": "^5.1.0",
    "svelte-check": "^4.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.6.0",
    "typescript-eslint": "^8.13.0",
    "vite": "^5.4.0",
    "vitest": "^2.1.0"
  },
  "dependencies": {
    "dompurify": "^3.2.0",
    "marked": "^14.1.0"
  }
}
```

- [ ] **Step 2: Create `svelte.config.js`**

```javascript
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: 'index.html',
      precompress: false,
      strict: true
    })
  }
};

export default config;
```

- [ ] **Step 3: Create `vite.config.ts`**

```typescript
import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [tailwindcss(), sveltekit()],
  test: {
    include: ['src/**/*.{test,spec}.{js,ts}'],
    environment: 'jsdom',
    setupFiles: ['./vitest-setup.ts'],
    globals: true
  }
});
```

- [ ] **Step 4: Create `tsconfig.json`**

```json
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "allowJs": true,
    "checkJs": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "sourceMap": true,
    "strict": true,
    "moduleResolution": "bundler"
  }
}
```

- [ ] **Step 5: Create `.gitignore`**

```gitignore
node_modules
/build
/.svelte-kit
/package
.env
.env.*
!.env.example
vite.config.js.timestamp-*
vite.config.ts.timestamp-*
```

- [ ] **Step 6: Create `.prettierrc`**

```json
{
  "useTabs": false,
  "singleQuote": true,
  "trailingComma": "none",
  "printWidth": 100,
  "plugins": ["prettier-plugin-svelte"],
  "overrides": [{ "files": "*.svelte", "options": { "parser": "svelte" } }]
}
```

- [ ] **Step 7: Create `.prettierignore`**

```
build
.svelte-kit
package
node_modules
```

- [ ] **Step 8: Create `eslint.config.js`**

```javascript
import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';
import prettier from 'eslint-config-prettier';
import globals from 'globals';
import ts from 'typescript-eslint';

export default ts.config(
  js.configs.recommended,
  ...ts.configs.recommended,
  ...svelte.configs['flat/recommended'],
  prettier,
  ...svelte.configs['flat/prettier'],
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node }
    }
  },
  {
    files: ['**/*.svelte'],
    languageOptions: { parserOptions: { parser: ts.parser } }
  },
  {
    ignores: ['build/', '.svelte-kit/', 'package/', 'node_modules/']
  }
);
```

- [ ] **Step 9: Create `.env.example`**

```env
PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 10: Install dependencies**

Run: `cd frontend && bun install`
Expected: creates `node_modules/` and `bun.lockb`, no errors.

- [ ] **Step 11: Verify TypeScript wiring**

Run: `cd frontend && bun run check`
Expected: 0 errors, 0 warnings (no source files yet — should still succeed).

- [ ] **Step 12: Commit**

```bash
git add frontend/package.json frontend/bun.lockb frontend/svelte.config.js frontend/vite.config.ts frontend/tsconfig.json frontend/.gitignore frontend/.prettierrc frontend/.prettierignore frontend/eslint.config.js frontend/.env.example
git commit -m "feat(frontend): Bootstrap SvelteKit + Tailwind v4 project"
```

---

## Task 4: App shell — Tailwind theme, font, SPA mode

**Files:**
- Create: `frontend/src/app.html`, `frontend/src/app.css`, `frontend/src/app.d.ts`
- Create: `frontend/src/routes/+layout.svelte`, `frontend/src/routes/+layout.ts`
- Create: `frontend/src/routes/+page.svelte` (placeholder for now)
- Create: `frontend/vitest-setup.ts`

- [ ] **Step 1: Create `src/app.html`**

```html
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap"
      rel="stylesheet"
    />
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover" class="bg-surface text-brand-ink">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

- [ ] **Step 2: Create `src/app.css`**

```css
@import 'tailwindcss';

@theme {
  --color-brand-red: #ce0033;
  --color-brand-coral: #f26f5c;
  --color-brand-ink: #123744;
  --color-surface: #ffffff;
  --color-surface-muted: #f4f1ee;
  --color-border-subtle: rgba(18, 55, 68, 0.12);

  --font-sans: 'Space Grotesk', ui-sans-serif, system-ui, sans-serif;
}

html,
body {
  font-family: var(--font-sans);
  min-height: 100vh;
}
```

- [ ] **Step 3: Create `src/app.d.ts`**

```typescript
declare global {
  namespace App {
    // interface Error {}
    // interface Locals {}
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }
}

export {};
```

- [ ] **Step 4: Create `src/routes/+layout.ts` (SPA mode)**

```typescript
export const prerender = true;
export const ssr = false;
```

- [ ] **Step 5: Create `src/routes/+layout.svelte`**

```svelte
<script lang="ts">
  import '../app.css';
  let { children } = $props();
</script>

<main class="mx-auto flex min-h-screen max-w-[760px] flex-col px-4 py-6">
  {@render children()}
</main>
```

- [ ] **Step 6: Create placeholder `src/routes/+page.svelte`**

```svelte
<h1 class="text-2xl font-bold tracking-wide">RAG Sample</h1>
<p class="text-brand-coral">Assistant IA</p>
```

- [ ] **Step 7: Create `vitest-setup.ts`**

```typescript
import '@testing-library/jest-dom/vitest';
```

- [ ] **Step 8: Smoke-test the dev server**

Run: `cd frontend && bun run dev`
Open `http://localhost:5173` in a browser.
Expected: page shows "RAG Sample" heading with Space Grotesk font; "Assistant IA" rendered in coral (`#F26F5C`). No console errors. Stop the server with Ctrl+C.

- [ ] **Step 9: Verify the build produces a static SPA**

Run: `cd frontend && bun run build`
Expected: a `build/` directory containing `index.html`, JS/CSS assets, no errors.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/app.html frontend/src/app.css frontend/src/app.d.ts frontend/src/routes frontend/vitest-setup.ts
git commit -m "feat(frontend): Add Tailwind v4 theme, app shell, and SPA routing"
```

---

## Task 5: Types and API client (with tests)

**Files:**
- Create: `frontend/src/lib/types.ts`
- Create: `frontend/src/lib/api/client.ts`
- Create: `frontend/src/lib/api/client.test.ts`

- [ ] **Step 1: Create types**

`frontend/src/lib/types.ts`:

```typescript
export type Role = 'user' | 'assistant';

export interface Message {
  id: string;
  role: Role;
  content: string;
  sources: string[];
  createdAt: number;
}

export type ChatStatus = 'idle' | 'connecting' | 'sending' | 'error';

export type ApiError =
  | { kind: 'network'; message: string }
  | { kind: 'http'; status: number; message: string };
```

- [ ] **Step 2: Write failing tests for the API client**

`frontend/src/lib/api/client.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest';
import { createConversation, sendMessage, ApiClientError } from './client';

const BASE = 'http://api.test';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('createConversation', () => {
  it('returns the conversation id on success', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ conversation_id: 'abc-123' }), { status: 200 })
      )
    );

    const id = await createConversation(BASE);

    expect(id).toBe('abc-123');
    expect(fetch).toHaveBeenCalledWith(`${BASE}/api/v1/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
  });

  it('throws ApiClientError with kind=http on non-2xx', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 500 })));
    await expect(createConversation(BASE)).rejects.toMatchObject({ kind: 'http', status: 500 });
  });

  it('throws ApiClientError with kind=network when fetch rejects', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(createConversation(BASE)).rejects.toMatchObject({ kind: 'network' });
  });
});

describe('sendMessage', () => {
  it('posts JSON content and returns content + sources', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ content: 'Hello', sources: ['s1', 's2'] }), { status: 200 })
      )
    );

    const result = await sendMessage(BASE, 'conv-1', 'Hi');

    expect(result).toEqual({ content: 'Hello', sources: ['s1', 's2'] });
    expect(fetch).toHaveBeenCalledWith(`${BASE}/api/v1/conversations/conv-1/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: 'Hi' })
    });
  });

  it('defaults missing sources to an empty array', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ content: 'Hi' }), { status: 200 }))
    );
    const result = await sendMessage(BASE, 'c', 'q');
    expect(result.sources).toEqual([]);
  });
});

it('ApiClientError is an Error subclass', () => {
  const e = new ApiClientError({ kind: 'http', status: 404, message: 'x' });
  expect(e).toBeInstanceOf(Error);
  expect(e.kind).toBe('http');
});
```

- [ ] **Step 3: Run tests, confirm they fail**

Run: `cd frontend && bun run test`
Expected: all client tests FAIL with import error (no `client.ts` yet).

- [ ] **Step 4: Implement the API client**

`frontend/src/lib/api/client.ts`:

```typescript
import type { ApiError } from '../types';

export class ApiClientError extends Error {
  readonly kind: ApiError['kind'];
  readonly status?: number;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'ApiClientError';
    this.kind = error.kind;
    if (error.kind === 'http') this.status = error.status;
  }
}

async function call<T>(input: string, init: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(input, init);
  } catch (err) {
    throw new ApiClientError({
      kind: 'network',
      message: err instanceof Error ? err.message : 'Network error'
    });
  }
  if (!response.ok) {
    throw new ApiClientError({
      kind: 'http',
      status: response.status,
      message: `HTTP ${response.status}`
    });
  }
  return (await response.json()) as T;
}

export async function createConversation(baseUrl: string): Promise<string> {
  const data = await call<{ conversation_id: string }>(`${baseUrl}/api/v1/conversations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  return data.conversation_id;
}

export async function sendMessage(
  baseUrl: string,
  conversationId: string,
  content: string
): Promise<{ content: string; sources: string[] }> {
  const data = await call<{ content?: string; sources?: string[] }>(
    `${baseUrl}/api/v1/conversations/${conversationId}/messages`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    }
  );
  return {
    content: data.content ?? '',
    sources: data.sources ?? []
  };
}
```

- [ ] **Step 5: Run tests, confirm they pass**

Run: `cd frontend && bun run test`
Expected: all 6 client tests PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/api
git commit -m "feat(frontend): Add typed API client with error handling"
```

---

## Task 6: Chat store with localStorage persistence (with tests)

**Files:**
- Create: `frontend/src/lib/stores/chat.svelte.ts`
- Create: `frontend/src/lib/stores/chat.test.ts`

- [ ] **Step 1: Write failing tests**

`frontend/src/lib/stores/chat.test.ts`:

```typescript
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushSync } from 'svelte';
import { createChatStore, STORAGE_KEY } from './chat.svelte';

const BASE = 'http://api.test';

function mockOnce(body: unknown, status = 200) {
  return vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(body), { status }));
}

beforeEach(() => {
  localStorage.clear();
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-05-11T12:00:00Z'));
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe('createChatStore', () => {
  it('init() creates a conversation and sets status to idle', async () => {
    vi.stubGlobal('fetch', mockOnce({ conversation_id: 'c-1' }));
    const chat = createChatStore(BASE);

    await chat.init();
    flushSync();

    expect(chat.conversationId).toBe('c-1');
    expect(chat.status).toBe('idle');
    expect(chat.messages).toEqual([]);
  });

  it('init() recovers state from localStorage without hitting the API', async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        conversationId: 'persisted',
        messages: [
          { id: 'm1', role: 'user', content: 'hi', sources: [], createdAt: 1 },
          { id: 'm2', role: 'assistant', content: 'hello', sources: ['s1'], createdAt: 2 }
        ]
      })
    );
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    const chat = createChatStore(BASE);
    await chat.init();
    flushSync();

    expect(fetchMock).not.toHaveBeenCalled();
    expect(chat.conversationId).toBe('persisted');
    expect(chat.messages).toHaveLength(2);
  });

  it('send() appends user then assistant message on success', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify({ conversation_id: 'c-1' })))
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ content: 'Bonjour', sources: ['s1'] }))
        )
    );

    const chat = createChatStore(BASE);
    await chat.init();
    await chat.send('Salut');
    flushSync();

    expect(chat.messages.map((m) => m.role)).toEqual(['user', 'assistant']);
    expect(chat.messages[1].content).toBe('Bonjour');
    expect(chat.messages[1].sources).toEqual(['s1']);
    expect(chat.status).toBe('idle');
  });

  it('send() sets status=error and keeps the user message on HTTP error', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify({ conversation_id: 'c-1' })))
        .mockResolvedValueOnce(new Response('boom', { status: 500 }))
    );

    const chat = createChatStore(BASE);
    await chat.init();
    await chat.send('Salut');
    flushSync();

    expect(chat.status).toBe('error');
    expect(chat.error?.kind).toBe('http');
    expect(chat.messages).toHaveLength(1);
    expect(chat.messages[0].role).toBe('user');
  });

  it('reset() clears messages, drops storage, and creates a new conversation', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify({ conversation_id: 'c-1' })))
        .mockResolvedValueOnce(new Response(JSON.stringify({ conversation_id: 'c-2' })))
    );

    const chat = createChatStore(BASE);
    await chat.init();
    chat.messages.push({
      id: 'm1',
      role: 'user',
      content: 'old',
      sources: [],
      createdAt: 1
    });
    await chat.reset();
    flushSync();

    expect(chat.conversationId).toBe('c-2');
    expect(chat.messages).toEqual([]);
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });
});
```

- [ ] **Step 2: Run tests, confirm they fail**

Run: `cd frontend && bun run test src/lib/stores`
Expected: tests FAIL (module not found).

- [ ] **Step 3: Implement the store**

`frontend/src/lib/stores/chat.svelte.ts`:

```typescript
import { ApiClientError, createConversation, sendMessage } from '../api/client';
import type { ApiError, ChatStatus, Message } from '../types';

export const STORAGE_KEY = 'rag-chat:v1';

interface PersistedState {
  conversationId: string | null;
  messages: Message[];
}

function loadFromStorage(): PersistedState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PersistedState;
    if (!parsed || typeof parsed !== 'object' || !Array.isArray(parsed.messages)) return null;
    return parsed;
  } catch {
    return null;
  }
}

function saveToStorage(state: PersistedState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Quota / serialization issues are non-fatal.
  }
}

function clearStorage(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

function toApiError(err: unknown): ApiError {
  if (err instanceof ApiClientError) {
    return err.kind === 'http'
      ? { kind: 'http', status: err.status ?? 0, message: err.message }
      : { kind: 'network', message: err.message };
  }
  return { kind: 'network', message: 'Unknown error' };
}

export function createChatStore(baseUrl: string) {
  let conversationId = $state<string | null>(null);
  let messages = $state<Message[]>([]);
  let status = $state<ChatStatus>('idle');
  let error = $state<ApiError | null>(null);

  $effect.root(() => {
    $effect(() => {
      if (conversationId !== null) {
        saveToStorage({ conversationId, messages });
      }
    });
  });

  async function init() {
    const persisted = loadFromStorage();
    if (persisted && persisted.conversationId) {
      conversationId = persisted.conversationId;
      messages = persisted.messages;
      status = 'idle';
      return;
    }
    status = 'connecting';
    error = null;
    try {
      conversationId = await createConversation(baseUrl);
      status = 'idle';
    } catch (err) {
      error = toApiError(err);
      status = 'error';
    }
  }

  async function send(content: string) {
    if (!conversationId) return;
    const trimmed = content.trim();
    if (!trimmed) return;

    messages.push({
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmed,
      sources: [],
      createdAt: Date.now()
    });
    status = 'sending';
    error = null;

    try {
      const response = await sendMessage(baseUrl, conversationId, trimmed);
      messages.push({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.content || 'Aucune réponse reçue.',
        sources: response.sources,
        createdAt: Date.now()
      });
      status = 'idle';
    } catch (err) {
      error = toApiError(err);
      status = 'error';
    }
  }

  async function reset() {
    clearStorage();
    messages = [];
    conversationId = null;
    error = null;
    status = 'connecting';
    try {
      conversationId = await createConversation(baseUrl);
      status = 'idle';
    } catch (err) {
      error = toApiError(err);
      status = 'error';
    }
  }

  return {
    get conversationId() {
      return conversationId;
    },
    get messages() {
      return messages;
    },
    get status() {
      return status;
    },
    get error() {
      return error;
    },
    init,
    send,
    reset
  };
}
```

- [ ] **Step 4: Run tests, confirm they pass**

Run: `cd frontend && bun run test src/lib/stores`
Expected: all 5 store tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/stores
git commit -m "feat(frontend): Add chat store with localStorage persistence"
```

---

## Task 7: Leaf components (TypingIndicator, SourcesPanel, ChatInput)

**Files:**
- Create: `frontend/src/lib/components/TypingIndicator.svelte`
- Create: `frontend/src/lib/components/SourcesPanel.svelte`
- Create: `frontend/src/lib/components/ChatInput.svelte`
- Create: `frontend/src/lib/components/ChatInput.test.ts`

- [ ] **Step 1: Create `TypingIndicator.svelte`**

```svelte
<div class="flex items-center gap-1 px-4 py-3" aria-label="Génération en cours">
  <span class="h-2 w-2 animate-bounce rounded-full bg-brand-coral [animation-delay:-0.3s]"></span>
  <span class="h-2 w-2 animate-bounce rounded-full bg-brand-coral [animation-delay:-0.15s]"></span>
  <span class="h-2 w-2 animate-bounce rounded-full bg-brand-coral"></span>
</div>
```

- [ ] **Step 2: Create `SourcesPanel.svelte`**

```svelte
<script lang="ts">
  let { sources }: { sources: string[] } = $props();
</script>

{#if sources.length > 0}
  <details class="mt-2 rounded-md border border-[color:var(--color-border-subtle)] px-3 py-2 text-sm">
    <summary class="cursor-pointer select-none font-medium text-brand-ink">
      📎 Sources ({sources.length})
    </summary>
    <ul class="mt-2 space-y-1 text-xs text-brand-ink/70">
      {#each sources as id (id)}
        <li class="font-mono">{id}</li>
      {/each}
    </ul>
  </details>
{/if}
```

- [ ] **Step 3: Write failing tests for `ChatInput`**

`frontend/src/lib/components/ChatInput.test.ts`:

```typescript
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import ChatInput from './ChatInput.svelte';

describe('ChatInput', () => {
  it('submits on Enter and clears the textarea', async () => {
    const onSubmit = vi.fn();
    render(ChatInput, { props: { disabled: false, onSubmit } });
    const user = userEvent.setup();

    const textarea = screen.getByPlaceholderText(/posez votre question/i);
    await user.type(textarea, 'Bonjour');
    await user.keyboard('{Enter}');

    expect(onSubmit).toHaveBeenCalledWith('Bonjour');
    expect((textarea as HTMLTextAreaElement).value).toBe('');
  });

  it('does NOT submit on Shift+Enter', async () => {
    const onSubmit = vi.fn();
    render(ChatInput, { props: { disabled: false, onSubmit } });
    const user = userEvent.setup();

    const textarea = screen.getByPlaceholderText(/posez votre question/i);
    await user.type(textarea, 'Line1');
    await user.keyboard('{Shift>}{Enter}{/Shift}');

    expect(onSubmit).not.toHaveBeenCalled();
    expect((textarea as HTMLTextAreaElement).value).toContain('\n');
  });

  it('does not submit empty/whitespace content', async () => {
    const onSubmit = vi.fn();
    render(ChatInput, { props: { disabled: false, onSubmit } });
    const user = userEvent.setup();

    const textarea = screen.getByPlaceholderText(/posez votre question/i);
    await user.type(textarea, '   ');
    await user.keyboard('{Enter}');

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('disables the send button when disabled prop is true', () => {
    render(ChatInput, { props: { disabled: true, onSubmit: vi.fn() } });
    expect(screen.getByRole('button', { name: /envoyer/i })).toBeDisabled();
  });
});
```

Add `@testing-library/user-event` to `frontend/package.json` devDependencies:

```bash
cd frontend && bun add -D @testing-library/user-event@^14.5.2
```

- [ ] **Step 4: Run tests, confirm they fail**

Run: `cd frontend && bun run test ChatInput`
Expected: tests FAIL (component not found).

- [ ] **Step 5: Implement `ChatInput.svelte`**

```svelte
<script lang="ts">
  interface Props {
    disabled: boolean;
    onSubmit: (text: string) => void;
  }

  let { disabled, onSubmit }: Props = $props();
  let value = $state('');
  let textarea: HTMLTextAreaElement | null = $state(null);

  function submit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    value = '';
    if (textarea) textarea.style.height = 'auto';
  }

  function onKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  function autosize() {
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  }
</script>

<form
  class="flex items-end gap-2 border-t border-[color:var(--color-border-subtle)] bg-surface pt-3"
  onsubmit={(e) => {
    e.preventDefault();
    submit();
  }}
>
  <textarea
    bind:this={textarea}
    bind:value
    oninput={autosize}
    onkeydown={onKeydown}
    rows="1"
    placeholder="Posez votre question…"
    class="min-h-[44px] flex-1 resize-none rounded-lg border border-[color:var(--color-border-subtle)] bg-surface px-3 py-2 text-brand-ink outline-none focus:border-brand-coral"
  ></textarea>
  <button
    type="submit"
    disabled={disabled || !value.trim()}
    class="rounded-lg bg-brand-red px-4 py-2 font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
  >
    Envoyer
  </button>
</form>
```

- [ ] **Step 6: Run tests, confirm they pass**

Run: `cd frontend && bun run test ChatInput`
Expected: all 4 ChatInput tests PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/lib/components/TypingIndicator.svelte frontend/src/lib/components/SourcesPanel.svelte frontend/src/lib/components/ChatInput.svelte frontend/src/lib/components/ChatInput.test.ts frontend/package.json frontend/bun.lockb
git commit -m "feat(frontend): Add leaf chat components (typing, sources, input)"
```

---

## Task 8: MessageBubble with Markdown + XSS sanitization

**Files:**
- Create: `frontend/src/lib/components/MessageBubble.svelte`
- Create: `frontend/src/lib/components/MessageBubble.test.ts`

- [ ] **Step 1: Write failing tests**

`frontend/src/lib/components/MessageBubble.test.ts`:

```typescript
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import MessageBubble from './MessageBubble.svelte';
import type { Message } from '../types';

function msg(overrides: Partial<Message> = {}): Message {
  return {
    id: 'm1',
    role: 'assistant',
    content: 'Hello',
    sources: [],
    createdAt: 0,
    ...overrides
  };
}

describe('MessageBubble', () => {
  it('renders user content as plain text (no Markdown parsing)', () => {
    const { container } = render(MessageBubble, {
      props: { message: msg({ role: 'user', content: '**bold**' }) }
    });
    expect(container.querySelector('strong')).toBeNull();
    expect(screen.getByText('**bold**')).toBeInTheDocument();
  });

  it('renders assistant Markdown as HTML', () => {
    const { container } = render(MessageBubble, {
      props: { message: msg({ content: 'Hello **world**' }) }
    });
    expect(container.querySelector('strong')?.textContent).toBe('world');
  });

  it('sanitizes script tags in assistant content', () => {
    const { container } = render(MessageBubble, {
      props: { message: msg({ content: 'safe <script>alert(1)</script>' }) }
    });
    expect(container.querySelector('script')).toBeNull();
    expect(container.textContent).toContain('safe');
  });

  it('renders SourcesPanel only when sources are present', () => {
    const { rerender } = render(MessageBubble, { props: { message: msg({ sources: [] }) } });
    expect(screen.queryByText(/sources/i)).toBeNull();

    rerender({ message: msg({ sources: ['chunk-1'] }) });
    expect(screen.getByText(/sources \(1\)/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests, confirm they fail**

Run: `cd frontend && bun run test MessageBubble`
Expected: FAIL (component missing).

- [ ] **Step 3: Implement `MessageBubble.svelte`**

```svelte
<script lang="ts">
  import DOMPurify from 'dompurify';
  import { marked } from 'marked';
  import type { Message } from '../types';
  import SourcesPanel from './SourcesPanel.svelte';

  let { message }: { message: Message } = $props();

  const html = $derived(
    message.role === 'assistant'
      ? DOMPurify.sanitize(marked.parse(message.content, { async: false }) as string)
      : ''
  );

  const isUser = $derived(message.role === 'user');
</script>

<div class="flex w-full {isUser ? 'justify-end' : 'justify-start'}">
  <div
    class="max-w-[85%] rounded-xl px-4 py-3 {isUser
      ? 'bg-brand-red text-white'
      : 'bg-surface-muted text-brand-ink'}"
  >
    {#if isUser}
      <p class="whitespace-pre-wrap break-words">{message.content}</p>
    {:else}
      <div class="prose-sm max-w-none break-words [&_pre]:overflow-x-auto [&_pre]:rounded-md [&_pre]:bg-brand-ink/10 [&_pre]:p-2 [&_code]:font-mono">
        {@html html}
      </div>
      <SourcesPanel sources={message.sources} />
    {/if}
  </div>
</div>
```

- [ ] **Step 4: Run tests, confirm they pass**

Run: `cd frontend && bun run test MessageBubble`
Expected: all 4 MessageBubble tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/MessageBubble.svelte frontend/src/lib/components/MessageBubble.test.ts
git commit -m "feat(frontend): Add message bubble with sanitized Markdown rendering"
```

---

## Task 9: MessageList, ChatHeader, page composition

**Files:**
- Create: `frontend/src/lib/components/MessageList.svelte`
- Create: `frontend/src/lib/components/ChatHeader.svelte`
- Modify: `frontend/src/routes/+page.svelte` (replace placeholder)

- [ ] **Step 1: Create `ChatHeader.svelte`**

```svelte
<script lang="ts">
  interface Props {
    onReset: () => void;
  }
  let { onReset }: Props = $props();
</script>

<header class="flex items-center justify-between border-b border-[color:var(--color-border-subtle)] pb-4">
  <div>
    <h1 class="text-3xl font-bold tracking-wide text-brand-ink">RAG Sample</h1>
    <p class="text-sm font-medium text-brand-coral">Assistant IA</p>
  </div>
  <button
    type="button"
    onclick={onReset}
    class="rounded-lg border border-[color:var(--color-border-subtle)] px-3 py-2 text-sm font-medium text-brand-ink transition-colors hover:bg-surface-muted"
  >
    Nouvelle conversation
  </button>
</header>
```

- [ ] **Step 2: Create `MessageList.svelte`**

```svelte
<script lang="ts">
  import type { ChatStatus, Message } from '../types';
  import MessageBubble from './MessageBubble.svelte';
  import TypingIndicator from './TypingIndicator.svelte';

  interface Props {
    messages: Message[];
    status: ChatStatus;
  }

  let { messages, status }: Props = $props();
  let scrollEl: HTMLDivElement | null = $state(null);

  $effect(() => {
    void messages.length;
    void status;
    if (scrollEl) scrollEl.scrollTop = scrollEl.scrollHeight;
  });
</script>

<div bind:this={scrollEl} class="flex-1 space-y-3 overflow-y-auto py-4">
  {#each messages as message (message.id)}
    <MessageBubble {message} />
  {/each}
  {#if status === 'sending'}
    <div class="flex justify-start">
      <div class="rounded-xl bg-surface-muted">
        <TypingIndicator />
      </div>
    </div>
  {/if}
  {#if messages.length === 0 && status === 'idle'}
    <p class="py-10 text-center text-sm text-brand-ink/60">
      Posez une première question pour démarrer la conversation.
    </p>
  {/if}
</div>
```

- [ ] **Step 3: Replace `+page.svelte` with the composed UI**

`frontend/src/routes/+page.svelte`:

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { env } from '$env/dynamic/public';
  import ChatHeader from '$lib/components/ChatHeader.svelte';
  import MessageList from '$lib/components/MessageList.svelte';
  import ChatInput from '$lib/components/ChatInput.svelte';
  import { createChatStore } from '$lib/stores/chat.svelte';

  const API_URL = env.PUBLIC_API_URL || 'http://localhost:8000';
  const chat = createChatStore(API_URL);

  onMount(() => {
    chat.init();
  });
</script>

<div class="flex h-[calc(100vh-3rem)] flex-col">
  <ChatHeader onReset={() => chat.reset()} />

  {#if chat.status === 'error' && chat.conversationId === null}
    <div class="my-auto flex flex-col items-center gap-3 text-center">
      <p class="text-brand-red">⚠️ Impossible de joindre l'API.</p>
      <button
        type="button"
        onclick={() => chat.init()}
        class="rounded-lg bg-brand-red px-4 py-2 font-medium text-white hover:opacity-90"
      >
        Réessayer
      </button>
    </div>
  {:else}
    <MessageList messages={chat.messages} status={chat.status} />

    {#if chat.status === 'error' && chat.conversationId !== null}
      <div
        class="mb-2 rounded-md border border-brand-red bg-brand-red/5 px-3 py-2 text-sm text-brand-red"
      >
        ⚠️ {chat.error?.message ?? "Erreur lors de l'envoi."}
      </div>
    {/if}

    <ChatInput
      disabled={chat.status === 'sending' || chat.status === 'connecting'}
      onSubmit={(text) => chat.send(text)}
    />
  {/if}
</div>
```

- [ ] **Step 4: Smoke-test end-to-end manually**

In one terminal, start the API:

```bash
cd api && uv run python main.py
```

In another, start the frontend:

```bash
cd frontend && bun run dev
```

Open `http://localhost:5173`. Verify:
- Header shows "RAG Sample" + "Assistant IA" + "Nouvelle conversation" button.
- The empty-state helper sentence appears.
- Type a question, press Enter → user bubble (red) appears on the right; typing indicator appears; assistant bubble (off-white) appears on the left with rendered Markdown.
- If the API returns sources, the `📎 Sources (N)` `<details>` is present.
- Refresh the page → previous messages reappear from localStorage; **no new conversation** is created (check API logs — no `POST /api/v1/conversations`).
- Click "Nouvelle conversation" → bubble area clears, a new conversation is created.
- Stop the API and try to send a message → red error banner above the input.

If any of the above fails, fix and rerun before continuing.

- [ ] **Step 5: Run full frontend test suite**

Run: `cd frontend && bun run test`
Expected: all tests PASS.

- [ ] **Step 6: Verify lint passes**

Run: `cd frontend && bun run lint && bun run check`
Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/lib/components/ChatHeader.svelte frontend/src/lib/components/MessageList.svelte frontend/src/routes/+page.svelte
git commit -m "feat(frontend): Compose chat page with header, list and error states"
```

---

## Task 10: CI workflow + pre-commit hook

**Files:**
- Create: `.github/workflows/frontend.yml`
- Modify: `.pre-commit-config.yaml`
- Modify: `.gitignore` (root)

- [ ] **Step 1: Add the CI workflow**

Create `.github/workflows/frontend.yml`:

```yaml
---
name: frontend

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend.yml'
  pull_request:
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend.yml'

jobs:
  lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest
      - run: bun install --frozen-lockfile
      - run: bun run lint
      - run: bun run check

  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest
      - run: bun install --frozen-lockfile
      - run: bun run test

  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest
      - run: bun install --frozen-lockfile
      - run: bun run build
```

- [ ] **Step 2: Add the frontend pre-commit hook**

Edit `.pre-commit-config.yaml`. After the existing `yamllint` hook, add inside the same `local` repo block:

```yaml
      - id: frontend-lint
        name: frontend lint (prettier + eslint)
        language: system
        entry: bash -c 'cd frontend && bun run lint'
        files: ^frontend/.*\.(ts|js|svelte|css|json)$
        pass_filenames: false
```

- [ ] **Step 3: Update root `.gitignore`**

Append:

```gitignore

# Frontend (SvelteKit)
frontend/node_modules
frontend/.svelte-kit
frontend/build
frontend/.env
```

- [ ] **Step 4: Run the hook locally to confirm it works**

Run: `pre-commit run frontend-lint --all-files`
Expected: PASS (assumes `bun install` was run in `frontend/`).

- [ ] **Step 5: Lint YAML**

Run: `uv run yamllint .github/workflows/frontend.yml`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/frontend.yml .pre-commit-config.yaml .gitignore
git commit -m "ci: Add frontend lint/test/build workflow and pre-commit hook"
```

---

## Task 11: Documentation updates

**Files:**
- Create: `frontend/README.md`
- Modify: `CLAUDE.md`, `docs/AGENTS.md`, `docs/TECHNICAL_GUIDE.md`, `docs/PROJECT_STRUCTURE.md`, `docs/FEATURES.md`, `docs/TASKS.md`, root `README.md`

- [ ] **Step 1: Create `frontend/README.md`**

```markdown
# Frontend

SvelteKit + Tailwind v4 chat UI for the RAG sample. Built as a static SPA via `@sveltejs/adapter-static`.

## Prerequisites

- [Bun](https://bun.sh) >= 1.1
- The API running locally (see `../api/README.md`)

## Setup

```bash
cd frontend
cp .env.example .env   # adjust PUBLIC_API_URL if your API is not on :8000
bun install
```

## Commands

| Command | Description |
|---|---|
| `bun run dev` | Start the dev server on `http://localhost:5173` |
| `bun run build` | Produce a static build in `build/` |
| `bun run preview` | Preview the production build on `http://localhost:4173` |
| `bun run test` | Run Vitest unit/component tests |
| `bun run lint` | Run Prettier + ESLint |
| `bun run format` | Apply Prettier formatting |
| `bun run check` | Type-check with `svelte-check` |

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `PUBLIC_API_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

The browser calls the API directly. The API must enable CORS for `http://localhost:5173` (already configured in `api/src/rag/api/app.py`).

## Stack

- SvelteKit 2 / Svelte 5 (runes)
- Tailwind CSS v4 (CSS-first theme in `src/app.css`)
- TypeScript (strict)
- Vitest + `@testing-library/svelte` + jsdom
- ESLint + Prettier
- `marked` + `DOMPurify` for Markdown rendering
```

- [ ] **Step 2: Update root `CLAUDE.md`**

Replace the "Frontend (Streamlit)" block in the "Quick commands" section with:

```bash
# Frontend (SvelteKit) — all commands run from frontend/
cd frontend
bun install                            # Install frontend dependencies
bun run dev                            # Run the SvelteKit dev server
bun run test                           # Run frontend tests
bun run lint                           # Lint + format check
```

- [ ] **Step 3: Update `docs/AGENTS.md`**

In the Tech Stack table, replace any "Streamlit" row with:

```markdown
| Frontend | SvelteKit 2 + Svelte 5 + TypeScript + Tailwind CSS v4 |
| Frontend package manager | Bun |
```

In the "Available Commands" block, replace the Streamlit lines with:

```bash
# Frontend (SvelteKit) — from frontend/
cd frontend
bun install
bun run dev
bun run test
bun run build
```

At the bottom of the file, replace the last-updated line with:

```markdown
*Last updated: 2026-05-11 — replaced Streamlit frontend with SvelteKit + Tailwind v4 SPA; added CORS middleware to FastAPI.*
```

- [ ] **Step 4: Update `docs/TECHNICAL_GUIDE.md`**

In the frontend section (find by searching for "Streamlit"), replace with a section that explains:
- SPA built with SvelteKit + `adapter-static` (no SSR)
- State in a runes-based store (`src/lib/stores/chat.svelte.ts`)
- API access via `fetch` to `PUBLIC_API_URL`, CORS allowed on the API
- Tests with Vitest + jsdom
- Local dev command, build output location, env vars

Concrete content:

```markdown
## Frontend

Static SPA built with **SvelteKit 2** (Svelte 5 runes) and **Tailwind CSS v4**. The build (`@sveltejs/adapter-static` with `fallback: 'index.html'`) produces a `frontend/build/` directory servable by any static host.

### Structure

- `src/routes/+page.svelte` — chat page composition
- `src/lib/components/` — `ChatHeader`, `MessageList`, `MessageBubble`, `SourcesPanel`, `TypingIndicator`, `ChatInput`
- `src/lib/stores/chat.svelte.ts` — runes-based store (`conversationId`, `messages`, `status`, `error`, plus `init`, `send`, `reset`)
- `src/lib/api/client.ts` — typed `fetch` wrapper
- `src/app.css` — Tailwind v4 `@theme` tokens (brand red `#CE0033`, coral `#F26F5C`, ink `#123744`)

### Backend coupling

The browser calls FastAPI directly using `PUBLIC_API_URL`. CORS is configured server-side via `CORS_ALLOWED_ORIGINS` (CSV; defaults to `http://localhost:5173,http://localhost:4173`).

### Tests

Vitest + `@testing-library/svelte` + jsdom. Covers: API client (success/HTTP/network), chat store (init from API or localStorage, send, error path, reset), `ChatInput` (Enter behavior, validation, disabled), `MessageBubble` (Markdown rendering + XSS sanitization).

### Persistence

The conversation (id + messages) is mirrored in `localStorage` under `rag-chat:v1` so reloads don't lose the local view of the conversation. The server-side persistence remains the source of truth.
```

- [ ] **Step 5: Update `docs/PROJECT_STRUCTURE.md`**

Replace the `frontend/` arborescence section with:

```text
frontend/
├── package.json, bun.lockb
├── svelte.config.js, vite.config.ts, tsconfig.json
├── eslint.config.js, .prettierrc, .prettierignore
├── .env.example
├── src/
│   ├── app.html, app.css, app.d.ts
│   ├── routes/+layout.svelte, +layout.ts, +page.svelte
│   └── lib/
│       ├── types.ts
│       ├── api/client.ts (+ tests)
│       ├── stores/chat.svelte.ts (+ tests)
│       └── components/{ChatHeader,MessageList,MessageBubble,SourcesPanel,TypingIndicator,ChatInput}.svelte (+ tests)
```

- [ ] **Step 6: Update `docs/FEATURES.md` and `docs/TASKS.md`**

In `docs/FEATURES.md`, add an entry under the relevant epic (Support Chatbot or equivalent) referencing the SvelteKit migration.

In `docs/TASKS.md`, move "Frontend migration to SvelteKit" from backlog to completed (or add and mark complete if absent).

Exact wording is at the implementer's discretion — keep it one bullet per file, in English.

- [ ] **Step 7: Update root `README.md`**

Replace any mention of "Streamlit" with "SvelteKit + Tailwind". Update the quickstart section to reference `bun install && bun run dev` from `frontend/`.

- [ ] **Step 8: Lint markdown**

Run: `uv run pymarkdownlnt scan --recurse .`
Expected: 0 errors. Fix anything reported.

- [ ] **Step 9: Final full-stack smoke test**

Repeat the manual smoke test from Task 9 Step 4 with the API and frontend running. Confirm everything still works after all subsequent changes.

- [ ] **Step 10: Commit**

```bash
git add frontend/README.md CLAUDE.md docs/AGENTS.md docs/TECHNICAL_GUIDE.md docs/PROJECT_STRUCTURE.md docs/FEATURES.md docs/TASKS.md README.md
git commit -m "docs: Update project docs for SvelteKit frontend migration"
```

---

## Final verification

- [ ] `cd api && uv run pytest` — all API tests pass
- [ ] `cd frontend && bun run test` — all frontend tests pass
- [ ] `cd frontend && bun run lint && bun run check` — clean
- [ ] `cd frontend && bun run build` — builds without errors
- [ ] `uv run pymarkdownlnt scan --recurse . && uv run yamllint .` — clean
- [ ] Manual end-to-end smoke test (API + frontend running) — chat works, sources panel works, reset works, refresh persists, error states render
