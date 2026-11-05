---
name: aspera
description: Have top models challenge and improve a code change, plan, opinion or review. In Testy McTestface, use an opposite-family child chat (Astra/Sol to Opus 5.5; Opus to Astra). Outside Testy, Codex consults Claude Opus 5.5; Claude and Cursor consult GPT-6 Astra. The manager verifies each finding, incorporates valid feedback within the authorized scope, and discusses contested points. Use when the user invokes /aspera or $aspera, or explicitly asks for this cross-model review.
disable-model-invocation: true
---

# Aspera: top models work together

You remain the owner. The other model is a peer who challenges your reasoning. Verify its claims against evidence; accept valid findings and explain rejected ones. The aim is a better result, not agreement or a second opinion pasted back to the user.

Use the folder containing this SKILL.md as `<skill dir>`. All harness installations should link to one checkout. Do not maintain separate host-specific instructions.

## 1. Define the review

Choose the explicit artifact first: code, diff, PR, plan, opinion or review. Otherwise use the latest substantive artifact in this chat. For text or a PR, save a local text snapshot. Include the exact revision and changed diff when reviewing code.

Write `target.md` and `brief.md` under `~/.cursor/aspera/inputs/<unique run>/`, or a task scratch folder. The brief states the goal, acceptance checks, scope, verified source paths/revisions, decisions, open questions and existing review evidence. Do not copy the full chat or secret values. Distinguish claims from verified results.

Reuse a current independent review that covers the same artifact, revision and risks. Review only changed or uncovered work. A missing, failed or incomplete review does not pass.

## 2. Select the peer and launch

Detect Testy McTestface first from the supplied environment and available `testy_*` tools. A Testy chat using Codex or Claude is still a Testy chat: use its native child-chat route, not either CLI.

| Invoking harness | Peer | Route |
| --- | --- | --- |
| Testy · Astra or Sol (Codex/OpenAI family) | Claude Opus 5.5 (`claude-opus-5-5`) | Testy child chat |
| Testy · Opus (Claude family) | GPT-6 Astra (`gpt-6-astra`) | Testy child chat |
| Codex, including Desktop | Claude Opus 5.5 (`claude-opus-5-5`) | Claude CLI |
| Claude Code | GPT-6 Astra (`gpt-6-astra`) | Codex CLI |
| Cursor | GPT-6 Astra (`gpt-6-astra`) | Codex CLI |

Use these top-model defaults at `xhigh` effort. Do not downgrade to Sol or Luna for this skill. Preserve an explicit user model choice. If a named model or CLI is unavailable, report the exact blocker; do not silently substitute. An Aspera invocation authorizes this cross-model review, not unrelated tasks or recursive reviewers.

### In Testy McTestface

1. Identify the manager's actual model family from the current chat, not the underlying Pi harness. For another Claude-family model, use Astra; for another Codex/OpenAI-family model, use Opus. If the family is unknown, report the routing ambiguity rather than guessing.
2. Call `testy_list_models` and select the peer's exact `profileID`. This selects both model and provider. If several profiles offer that model, use the current provider when applicable; otherwise use an available authenticated profile. Never rely on an ambiguous model name or a `default` alias.
3. Call `testy_create_thread` with that `profileID`, `reasoning: "xhigh"`, the current chat ID as `coordinatorID`, and the current `projectID`. Give it a clear review title and a compact brief with the artifact paths and revision. Use a fresh request UUID; reuse it only to recover the same create request after a lost response.
4. Explicitly tell the peer: review only; do not edit, publish, expose secrets, invoke Aspera, or create more reviewers. Testy does not provide the CLI's read-only sandbox for this child; these are task constraints, not a permission boundary. Report any required access it lacks.
5. Retain the returned child ID. Use `testy_wake_on_thread` with a deadline, then end the turn. On wake, read the complete result with `testy_read_thread` and verify its model/profile and coverage. A failed, stopped, empty or incomplete reply is not a completed review.
6. Send focused follow-ups to the same child with `testy_send_prompt`. Wait for its next reply in the same way. Do not launch a replacement peer for a rebuttal.

If native tools or the required peer profile are unavailable, report the exact blocker. Do not silently use a CLI instead. An existing review child for the same revision remains the owner; reuse it.

### Outside Testy: CLI route

```bash
bash "<skill dir>/scripts/aspera.sh" --from <codex|claude|cursor> \
  --target "<target file>" --brief "<brief file>" --cd "<source root>"
```

Always supply the actual invoking harness. Old callers outside Codex retain the Cursor default. If `CODEX_THREAD_ID` is set, an omitted `--from` fails rather than routing to the wrong peer. Overrides are `ASPERA_MODEL` (full canonical model ID), `ASPERA_EFFORT` and `ASPERA_OUT_DIR`. State which model is reviewing. Do not leave an old model override in place if it conflicts with this request.

The reviewer is read-only. Claude gets Read, Glob and Grep inside the working directory and the target/brief directories. Codex uses its read-only sandbox. Put needed diff/source evidence in the packet if those tools cannot reach it. Report access limits; do not broaden permissions to hide them. Claude's JSON receipt must identify the requested model and contain a successful, nonempty review.

## 3. Wait on the owner

Before waiting, record the completion condition, owner process/run, next action, wake mechanism and deadline. Use the host's supported background completion wait: Testy's `testy_wake_on_thread`, Cursor AwaitShell, Claude's task completion, or Codex's command-session completion. Keep one owner and one waiter. Do not add log-reading or sleep loops. On a bounded timeout, retain the owner. If no event wake exists, state the next manual check; do not claim ongoing monitoring.

Exit 75 identifies an existing owner and run. Reuse it. Remove a stale lock only after proving that owner and its reviewer process have stopped. A lock is not a review receipt.

## 4. Verify, reconcile and discuss

On a completed Testy child reply or `ASPERA_DONE <path>`, read the full review. Check each actionable claim against the artifact, code and meaningful tests. Record **accepted**, **rejected with evidence**, or **unresolved**. Preserve the reviewer's original report; keep your disposition separate.

Incorporate accepted findings into the work already authorized. A review-only request authorizes an assessment and proposed corrections, not source edits or external writes. Do not ask for permission again when implementation is already authorized.

For a disputed material finding or a substantive correction, send a focused reply to the same peer model. The next brief includes the prior review, your evidence and reasoning, accepted/rejected findings, and the revised artifact or exact diff. In Testy, send that packet to the same child chat. Outside Testy, run the launcher again with that packet. CLI calls are isolated, so include the prior discussion explicitly. Ask the peer to check the rebuttal and changed scope. Verify its answer in turn. Do not recursively invoke Aspera from the reviewer or run duplicate broad reviews.

Normally use one independent pass and one focused response. Stop when the required checks pass and no supported blocker remains. If two exchanges make no progress, report the unresolved point and evidence instead of looping or accepting a claim by authority. Agreement alone is not proof.

## 5. Report

Give the outcome, valid findings and their disposition, meaningful disagreements, checks, limits, and review path. Name the actual peer model. On `ASPERA_FAILED`, report the exit code and a redacted cause from the local log/result. Never paste raw logs that could contain secrets. CLI success means a report arrived; the manager still decides whether the task passes.
