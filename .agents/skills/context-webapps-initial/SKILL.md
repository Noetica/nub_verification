---
name: context-webapps-initial
description: Build a first-pass context pack for a frontend or mixed web repository, where RepoMap adds little. Use when bootstrapping context for a web or mixed repo.
---

# Context Pack — Web App Initial Pass

You are producing a concise first-pass developer context pack for a frontend or mixed web application repository.

This prompt replaces the .NET-oriented initial pass for frontend repositories, and for mixed web repositories where RepoMap is not available or is not useful for the frontend/web slice. It combines the narrative context gathering of the standard initial pass with a lightweight structural analysis covering entry points, routing, state management, API boundaries, probable hotspots, and probable refactoring seams.

## Goals

1. Build or update `docs/context-pack/overview.md` with both narrative context and structural analysis.
2. Keep content short, evidence-based, and easy to refresh.
3. Update `README.md` and `AGENTS.md` so they keep the current Context Pack entry-point links.

## Rules

- Follow the shared evidence, idempotency, and entry-point link conventions in `.agents/shared/context-pack-links.md`.
- Stay concise: aim for ~3 pages total in `overview.md`; prefer bullets/tables over long prose.
- If the repo contains a server-side .NET component alongside the frontend, note it in overview.md as a subsystem but do not attempt deep .NET analysis. Suggest running RepoMap separately for that component if deeper analysis is wanted.

## Steps

### 1. Detect stack and framework

Scan for framework indicators and identify:
- **Primary framework(s)**: check `package.json` dependencies, `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `angular.json`, `vue.config.*`, `nuxt.config.*`, `vite.config.*`, `next.config.*`, `remix.config.*`, `astro.config.*`, `svelte.config.*`, `webpack.config.*`, `.babelrc`, `tsconfig.json`.
- **Server-side component**: check for `.csproj` with Web SDK, `Startup.cs`, `Program.cs`, `web.config`, or equivalent backend indicators.
- **Legacy patterns**: check for Knockout.js references in NuGet packages, script bundles, or `<script>` tags in views.
- **Language**: TypeScript, JavaScript, TSX/JSX, or mixed.
- **Build tooling**: Vite, Webpack, Angular CLI, Vue CLI, Next/Nuxt build pipeline, Turborepo/Nx workspace tooling, MSBuild bundling, script bundles, etc.

### 2. Scan repo structure

Identify:
- Core purpose and boundaries
- Main components/subsystems
- Key integrations (APIs, services, databases, queues)
- Critical flows and known fragility points (if observable)

### 3. Structural analysis

Gather evidence for each of the following. Skip any category that does not apply to the detected stack.

- **App bootstrap and entry points**: `main.ts`/`main.js`, `index.html`, `src/main.tsx`, root app module/component, filesystem-routing roots such as `app/`, `pages/`, `routes/`, server-side `Startup.cs`/`Program.cs` if mixed.
- **Router structure**: route definitions, filesystem routing, lazy-loaded modules/chunks, guards, middleware, layout nesting, server-side route registration if mixed.
- **State management**: stores (Vuex, Pinia, NgRx, Redux, MobX, Zustand), React context providers, services used as singletons, Knockout view models, shared state patterns.
- **API boundaries**: HTTP client usage (`axios`, `fetch`, `HttpClient`, `$.ajax`), API base URL configuration, service layers that wrap HTTP calls, server actions/loaders, BFF or API route handlers where applicable.
- **Component/module inventory**: top-level feature modules or feature folders, high-fan-in shared/common directories, layout components.
- **Probable hotspots** `HEURISTIC`: largest files by line count, files with the most imports or exports, files that touch many concerns (routing + state + API in one file), deeply nested component trees.
- **Probable seams/risks** `HEURISTIC`: tight coupling between components and API clients, global state mutations from many call sites, large monolithic components, mixed server/client responsibility in views, significant duplication across feature modules.

For framework-specific stacks, adapt the analysis rather than forcing SPA terminology:
- **Next.js / Nuxt / Remix / SvelteKit / Astro**: include filesystem-routing conventions, server/client boundaries, middleware, loaders/actions/server routes, and API handlers.
- **React apps without framework routing**: look for `src/main.tsx`, `src/App.tsx`, router setup, context providers, and feature-folder boundaries.
- **Workspace repos**: identify the app package(s), shared UI packages, and any backend-for-frontend package separately.

### 4. Write overview.md

Create or update `docs/context-pack/overview.md` with these sections:

| Section | Content |
|---|---|
| **Repo Summary** | Purpose, primary tech, team ownership if known |
| **Stack and Tooling** | Framework(s), language, build tool, server component if any |
| **Architecture at a glance** | Table of areas/responsibilities with evidence citations |
| **Key Flows (top 3)** | Most important user or data flows through the system |
| **Web Structure** | Entry points, routes, state management, API boundaries, probable hotspots, probable seams — all from step 3 |
| **Integrations** | External APIs, databases, queues, auth providers |
| **Risks / Unknowns** | Mark unknowns clearly; tag unverified claims |

### 5. Update README.md and AGENTS.md

Update the `Context Pack` index section in both `README.md` and `AGENTS.md` per `.agents/shared/context-pack-links.md` — in mixed repos, take particular care to preserve existing RepoMap links.

## Output

- Apply edits directly to the files above.
- End with a short change summary and list unresolved unknowns.
