# Git workflow (keep it simple)

- `main` is always demo-able. **Don't push to main directly** — open a PR, have one teammate review.
- One branch per task: `feat/<task>-<short-name>`, e.g. `feat/ml-zip-model`, `feat/ui-floor-checklist`.
- Commit small and often: `feat: ...`, `fix: ...`, `docs: ...`.
- Before opening a PR: `git pull origin main --rebase`, then `pytest` (backend) / `npm run lint && npm run build` (frontend).
- Never commit `.env`, `venv/`, `node_modules/`, or real keys. If a key leaks, rotate it immediately.
- Touching the API shape? Update the Pydantic model **and** `frontend/src/lib/types.ts` in the same PR, and tell the team.

```bash
git checkout main && git pull
git checkout -b feat/ml-zip-model
# ...work...
git add -A && git commit -m "feat: ZIP baseline per SKU"
git push -u origin feat/ml-zip-model     # then open a PR on GitHub
```
