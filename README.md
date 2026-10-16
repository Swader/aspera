# Aspera

Aspera makes top models work together. Your agent sends code, a plan, an opinion or a review to a peer in another harness, verifies the response, incorporates valid findings within scope, and discusses disputed points with evidence.

| Manager's harness | Review peer |
| --- | --- |
| Codex | Claude Opus 5.5 (`claude-opus-5-5`) through Claude CLI |
| Claude Code or Cursor | GPT-6 Astra (`gpt-6-astra`) through Codex CLI |

Both default to `xhigh`. There is no silent downgrade. The manager remains accountable; agreement is not proof. A review-only request remains read-only.

## Install once, link each harness

Requirements: Bash, Git, Python 3, and the peer CLI installed and authenticated with access to the selected model.

For a fresh installation:

```bash
git clone https://github.com/Swader/aspera.git "$HOME/.cursor/skills/aspera"
mkdir -p "$HOME/.claude/skills" "$HOME/.agents/skills"
ln -s "$HOME/.cursor/skills/aspera" "$HOME/.claude/skills/aspera"
ln -s "$HOME/.cursor/skills/aspera" "$HOME/.agents/skills/aspera"
```

If a destination exists, compare it and save its changes before replacing it with a symlink. Do not create a second Codex copy in another discovery directory. Codex discovers global skills in `~/.agents/skills`; Cursor and Claude use their own skills directories. All links above resolve to the same Git checkout. The skill uses paths relative to its own directory and also works when that checkout lives elsewhere.

Invoke `/aspera` in Cursor or Claude, or `$aspera` in Codex. See [SKILL.md](SKILL.md) for the shared review and discussion workflow.

## Runner

```bash
bash /path/to/aspera/scripts/aspera.sh --from codex \
  --target /path/to/target.md --brief /path/to/brief.md --cd /path/to/source
```

Use `--from claude` or `--from cursor` for the Astra route. Omission retains the Cursor route for old callers outside Codex; it fails when `CODEX_THREAD_ID` is set. `ASPERA_MODEL` overrides the full canonical model ID; `ASPERA_EFFORT` overrides effort. Claude model aliases are not accepted as verified receipts: use the exact ID returned by the provider. `ASPERA_OUT_DIR` defaults to `~/.cursor/aspera` for existing run/lock continuity.

Runs contain the prompt, log and `review.md`; Claude runs also retain `result.json` with the model receipt. `ASPERA_DONE` confirms a nonempty report arrived. Failures, malformed results and mismatched Claude model receipts fail. The manager still checks coverage, findings and acceptance.

Identical concurrent inputs share one owner. Exit 75 reports its PID and run. Reuse that owner. Verify both owner and reviewer stopped before removing a stale lock. Interrupts stop the reviewer before releasing ownership.

Claude runs with only Read, Glob and Grep, confined to the working and input directories. Codex uses a read-only sandbox. Put unavailable source or diff evidence into the input packet; missing access is a reported limit. No reviewer may edit, publish, spawn recursive reviewers or expose secrets. Follow-up calls receive the prior review, manager's evidence and changed artifact in a new brief, so the discussion remains explicit and reviewable.
