---
name: aspera
description: Sends the latest artifact from the current chat (a plan file, an answer, a PR or diff) to Astra (Codex CLI, gpt-6-astra at xhigh effort) for an adversarial review, judged for simple code, full functionality, low tech debt and proven at-scale practice (caching, parallelism, non-blocking queues, 10x opportunities). Then reports the findings. Use when the user invokes /aspera or asks for an Astra review.
disable-model-invocation: true
---

# Aspera: Astra adversarial review

Skill dir: `~/.cursor/skills/aspera`. Put the files you write (`target.md`, `brief.md`) in an input dir, `~/.cursor/aspera/input-<YYYYmmdd-HHMMSS>/`. The script makes its own run dir for `review.md` and `codex.log`.

## 1. Pick the target

In this order:
1. An explicit argument after `/aspera` (file path, PR URL, pasted text). Write pasted text to `<input dir>/target.md`.
2. The file most recently created or edited in this chat (for example a plan `.md`).
3. Otherwise, write the last substantive assistant answer to `<input dir>/target.md`.

For a PR or diff, write the diff (`gh pr diff`, `git diff`) and the PR link to `<input dir>/target.md`.

## 2. Write the brief

`<input dir>/brief.md`, a few lines only:
- What the target is.
- The user's goal in this chat (1-3 sentences).
- Repos involved: absolute local checkout path, and the branch and commit you read them at (`git rev-parse HEAD`).
- Links to PRs and issues mentioned.

Never include secret values. Do not paste the whole chat.

## 3. Run in the background

Shell tool with `block_until_ms: 0`, from the target's repo root:

```bash
bash "$HOME/.cursor/skills/aspera/scripts/aspera.sh" \
  --target "<file>" --brief "<input dir>/brief.md" [--cd "<repo root>"]
```

`--cd` defaults to the git toplevel of the target's directory. Overrides: `ASPERA_MODEL` (default `gpt-6-astra`), `ASPERA_EFFORT` (default `xhigh`), `ASPERA_OUT_DIR` (default `~/.cursor/aspera`).

Tell the user in one sentence that Astra is reviewing and that an xhigh review can take 10-40 minutes.

## 4. Wait without polling

Use the native AwaitShell tool with `pattern: "ASPERA_(DONE|FAILED)"` and a long block time. If it times out, await again. Do not read the log in a loop.

## 5. Report

- On `ASPERA_DONE <path>`: read `review.md`. Present Astra's findings result first, in plain, short language. Keep Astra's severity and order. Mark which findings you spot-checked against code.
- Do not apply changes unless the user asks. A review authorizes an assessment, not an implementation.
- On `ASPERA_FAILED exit=<code> log=<path>`: show the exit code and the last log lines, and name the cause (for example: codex not on PATH, auth failure, unknown model, missing target).
- Give the `review.md` path. Codex keeps the session, so the user can continue it with `codex resume`.
