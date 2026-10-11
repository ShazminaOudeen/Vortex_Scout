# Contributing to Scout

This guide describes how Team Vortex works on this repository. 

## Table of Contents

1. [Ground Rules](#ground-rules)
2. [Development Setup](#development-setup)
3. [Workflow](#workflow)
4. [Branches and Commits](#branches-and-commits)
5. [Pull Requests](#pull-requests)
6. [Testing](#testing)
7. [Code Guidelines](#code-guidelines)
8. [Secrets and Shared Data](#secrets-and-shared-data)
9. [Working With AI Tools](#working-with-ai-tools)
10. [Keeping the Documentation Honest](#keeping-the-documentation-honest)
11. [Troubleshooting](#troubleshooting)

---

## Ground Rules

- `main` is protected. Nothing is pushed to it directly; every change arrives through a pull request.
- One feature, one branch, one pull request. Small pull requests are reviewed faster and break less.
- Every change is tested before it is submitted. `main` must always run.
- Secrets never enter the repository. If one does, rotate it immediately (see [Secrets and Shared Data](#secrets-and-shared-data)).
- The demo must be real. If something is mocked, the README says so.

---

## Development Setup

Prerequisites: Python 3.12, Node.js 20 or later, Git. Windows users should use Git Bash for the commands below.

### Backend

```
cd backend
python -m venv venv
source venv/bin/activate            # Windows Git Bash: source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

Check that your prompt shows `(venv)` before running any backend command. Many "No module named ..." errors come from a terminal where the virtual environment is not active.

### Frontend

```
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The app runs without any API keys. Without Supabase credentials the backend uses an in-memory store, and without a Gemini key the checklist uses a template briefing. Full environment variable documentation is in the README.

---

## Workflow

Contributors work from a fork of the repository.

1. Fork `ShazminaOudeen/Vortex_Scout` on GitHub and clone your fork.
2. Add the original repository as `upstream` (one time):
   ```
   git remote add upstream https://github.com/ShazminaOudeen/Vortex_Scout.git
   ```
3. Before starting any new work, bring your `main` up to date:
   ```
   git checkout main
   git fetch upstream
   git merge upstream/main
   git push origin main
   ```
   The **Sync fork** button on your fork's GitHub page does the same job.
4. Create a branch, do the work, push the branch to your fork, and open a pull request against `main` of the original repository.
5. After your pull request is merged, sync your fork again before starting the next feature.

If you have write access to the main repository you may push branches there instead of using a fork. The rest of the workflow is identical.

Pick a feature from the team plan and tell the group before you start, so two people do not build the same thing.

---

## Branches and Commits

### Branch names

```
feat/<feature-id>-<short-name>      feat/B3-zip-model
fix/<short-name>                    fix/floor-empty-state
docs/<short-name>                   docs/readme-status-table
test/<short-name>                   test/detector-edge-cases
```

Use the feature ID from the team plan where there is one.

### Commit messages

Use a type prefix, a short imperative summary, and keep the first line under about 72 characters.

| Type | Use for |
|---|---|
| `feat` | A new capability |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `test` | Adding or correcting tests |
| `refactor` | Restructuring without behaviour change |
| `chore` | Tooling, dependencies, configuration |

Examples: `feat: add zero-inflated Poisson scorer`, `fix: handle empty checklist on floor page`.

Commit small and often. A branch with a clear sequence of commits is easier to review than one large commit.

---

## Pull Requests

1. Update your branch first: `git pull upstream main --rebase` (or merge `upstream/main`). Resolve conflicts locally.
2. Run the checks in [Testing](#testing). Do not open a pull request with failing checks.
3. Open the pull request and complete the template. State clearly:
   - what the change does and which feature ID it covers,
   - how a reviewer can test it,
   - what is still missing or mocked,
   - screenshots for any visible UI change.
4. At least one teammate reviews before merge. Reviewers pull the branch and run it, rather than only reading the diff.
5. Resolve review comments, then **squash and merge**. This keeps one clean commit per feature on `main`.
6. Delete the branch after merging.

Changes that alter an API response must update the Pydantic models in `backend/app/models/` and `frontend/src/lib/types.ts` in the same pull request, and the team should be told. Prefer additive changes (new fields) over renaming or removing fields.

---

## Testing

### Backend

```
cd backend
pytest -q
```

The suite runs without network access or API keys. Data-layer and endpoint tests run twice: once against the in-memory store and once through the Supabase code paths with a fake client.

- New backend logic needs tests. Use the shared fixtures in `tests/conftest.py` so your tests run against both stores.
- `tests/conftest.py` stops tests from calling the real Gemini API even when your `.env` contains a key. Do not remove that guard.
- A passing run against the fake client does not prove the real database path works. When you change anything that touches Supabase, try it once against a real project and say so in the pull request.

### Frontend

```
cd frontend
npm run lint
npm run build
```

Both must pass. For UI changes, also open the page in a browser and check the empty, loading and error states.

---

## Code Guidelines

### Backend (Python)

- Keep route handlers thin. Business logic belongs in `app/services/` and `app/ml/`.
- All database access goes through `app/core/store.py`, so the in-memory and Supabase paths stay in step.
- Detection and scoring code in `app/ml/` should be pure functions of a data frame, which makes it easy to test without a database.
- Use type hints and Pydantic models for request and response bodies.
- Do not hardcode values that belong in settings (`app/core/config.py`).

### Frontend (TypeScript)

- Pages fetch data through the hooks in `src/hooks/` and the client in `src/lib/api.ts`.
- Shared types live in `src/lib/types.ts`.
- Sample data lives only in `src/lib/mock.ts`. Do not scatter hardcoded numbers through components.
- Style with Tailwind classes and reuse the components in `src/components/`.

### General

- Prefer clear names over comments, and comments that explain why rather than what.
- Remove debugging code and unused files before committing.

---

## Secrets and Shared Data

- Never commit `.env`, `.env.local`, `venv/`, `node_modules/`, or any key. Check `git status` before every commit.
- The Supabase **service_role** key has full database access. It belongs only in `backend/.env`. It must never appear in frontend code, in a variable starting with `NEXT_PUBLIC_`, in screenshots, or in chat messages. Share keys privately, one to one.
- If a key leaks, rotate it straight away: regenerate the Supabase key under Project Settings, API Keys, and create a new Gemini key in Google AI Studio.
- The team shares one Supabase project. These actions change shared data:
  - `python -m app.generator.seed` deletes the demo tables and reloads them.
  - `POST /api/v1/simulate/reset` deletes all sales history in the connected database.
  - Injecting phantom stockouts adds sales rows for everyone.
- Run destructive scripts against your own in-memory store (leave Supabase keys unset) whenever you can.

---

## Working With AI Tools

AI coding assistants are allowed and encouraged for this project. The Buildathon requires an honest AI Usage Report, so:

- Review everything an assistant produces. Read the diff, run the tests, and run the feature yourself.
- Never paste secrets into a prompt, and keep `.env` files closed while an assistant is attached to your editor.
- Do not let an agent commit to `main`, push, or run destructive scripts (seed, reset) against the shared database.
- In your pull request description, add a line stating which tool helped and with what, for example: "AI assistance: Antigravity for the first draft of the KPI endpoint; hand-edited and tested."
- If an assistant produced something wrong or unusable, note it in the pull request. These examples go into the AI Usage Report.
- Every statistic, figure or citation that appears in documents must be verifiable. Do not publish numbers an assistant produced without checking them.

---

## Keeping the Documentation Honest

The README contains a table of what is functional, partial, mocked and planned. When your pull request changes the status of a feature, update that table in the same pull request. Judges respect a clearly marked mock; they do not respect finding one.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No module named ...` when running Python | Activate the virtual environment: `source venv/Scripts/activate` (Git Bash on Windows). |
| `bash: venvScriptsactivate: command not found` | Git Bash needs forward slashes: `source venv/Scripts/activate`. |
| Tests take several minutes | Pull the latest `main`; the test guard that blocks real Gemini calls must be present. |
| Gemini returns 404 for the model | Google retires models often. Set `GEMINI_MODEL` in `backend/.env` to a current model. |
| Gemini returns 503 | The model is overloaded. The app retries and falls back to a template sentence. Try again in a minute. |
| Backend returns empty data after setting Supabase keys | Check that `SUPABASE_KEY` is the secret / service_role key, not the publishable key. |
| Merge conflicts | Update your branch from `upstream/main`, resolve locally, and re-run the tests before pushing. If you are unsure, ask before forcing anything. |
| A key was committed | Rotate it first, then ask the Team Lead how to clean the history. |

