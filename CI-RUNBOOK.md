# CK PF native Windows validation via GitHub Actions - RB6j runbook (Route A)

Runs the native Windows validation kit (validation/windows-kit, kit RB6g) on a
GitHub-hosted windows-latest runner. Route A: everything moves over the
per-repo write deploy key (ssh alias gh-ckpf-write on the VPS). No API token,
no gh CLI, no credentials in any message.

## Guarantees (changed from RB6g - auditor must re-PASS these)
- The run starts ONLY when a repo writer pushes a branch named exactly
  `windows-validation-run`. One push = one run. No pull_request, no schedule,
  no workflow_dispatch, no other trigger. (RB6g was manual dispatch only;
  dispatch is impossible without an API token, so deliberateness now comes
  from the named-branch push, an explicit act by the deploy-key holder.)
- 30-minute hard cap (timeout-minutes: 30). At the standard Windows runner
  rate ($0.010/min, verified 2 Nov 2026) one run draws at most $0.30 from the
  repo owner's monthly included compute usage ($12 GitHub Free / $18 Pro).
  With no payment method on file, or a $0 spending limit, no charge is
  possible - usage is blocked at the allowance.
- concurrency group windows-validation with cancel-in-progress bounds
  accidental double pushes to one active run.
- The kit's S1 gate re-verifies the candidate zip sha256 against the RB6g
  pin (75049126...) on the runner itself before anything launches.

## Push order (all via gh-ckpf-write; nothing before Mani's approval)
1. main: add .github/, validation/, CI-RUNBOOK.md from this bundle
   (additive-only commit; touches no existing file). Push.
2. Branch candidate-rb6g from main: add ck-personal-finance-windows-v1.0.zip
   (35,138,081 B, sha256 75049126...; recorded in the commit message). Push.
   This branch is the interim durable private home for the candidate bytes.
3. LAST, to start the run: branch windows-validation-run from main, one empty
   commit, push. The workflow starts on that push.
4. Delete windows-validation-run after the run (keeps the trigger one-shot).

## Evidence retrieval (no API token)
The workflow pushes the kit's results folder to branch
windows-validation-evidence-<run_id> (auto GITHUB_TOKEN, contents: write).
The step fails loudly (exit 1) if the kit produced no results folder or
nothing new to commit - empty or missing evidence can never look green.
On the VPS: git fetch origin, then read the branch. The same folder is also
uploaded as artifact ckpf-windows-validation-evidence (retention 30 days) for
any later browser/API retrieval.

## What the run proves / does not prove
- The candidate zip's sha256 matches the audited pin; the app starts and
  serves natively on Windows, driven by Windows PowerShell 5.1.
- The 1190-file bundle manifest verifies; bundled tesseract 5.5.4 runs
  natively on Windows.
- The synthetic OCR flow works end-to-end on Windows: PNG bill, 4-frame
  TIFF (3 read + skip notice), 2-page PDF; confirm writes a bill; the bill
  persists across an app restart; Ask without Ollama returns a clean 503
  message; Stop-Ledger frees the port; no leftover working rasters.

## What it does NOT prove
- Consumer Windows 10/11 desktop (the runner is Windows Server).
- SmartScreen / antivirus reputation prompts on a home PC.
- Interactive GUI behaviour; the run is API-level.
- Phone behaviour (separately: "not yet checked on phones" stays on the
  page until Mani tests).
