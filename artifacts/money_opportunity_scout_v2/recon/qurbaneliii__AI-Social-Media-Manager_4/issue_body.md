## Summary
GitHub Pages deployment for the frontend is failing intermittently due to Next.js static export incompatibilities with App Router API routes and dynamic route settings.

## Current behavior
- Build can fail with import resolution/type errors when API routes are moved incorrectly during Pages build.
- Static export fails when `app/api` is included.
- Dynamic route config can block export when not aligned with `output: export`.

## Expected behavior
Frontend should deploy reliably to GitHub Pages from `main` and publish the latest static build (`aria-frontend/out`) without manual intervention.

## Scope
- Stabilize Pages workflow for static export.
- Keep App Router API routes excluded from static export path safely.
- Ensure dynamic route configuration remains export-compatible.
- Add guardrails to avoid regressions in CI.

## Acceptance criteria
1. GitHub Pages workflow passes on push to `main`.
2. No `Cannot find module '@/app/api/ai/_lib'` errors in build logs.
3. Static export completes and uploads Pages artifact successfully.
4. Published site serves latest frontend version without 404 root error.
