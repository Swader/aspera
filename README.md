# Aspera

Aspera is an agent skill. It sends your agent's latest artifact (a plan file, an answer, or a PR diff) to Astra through the [Codex CLI](https://github.com/openai/codex) for an adversarial review. Then your agent reports the findings in plain language.

The review checks for simple code, full functionality and low tech debt. It also checks for practices that have proven themselves at scale: caching, parallelism, non-blocking async queues, and any clear 10x gain in performance or cost. Astra reads the real code, including other repos the artifact touches, and ends with a prioritized list of improvements with `file:line` evidence.

## Requirements

- `bash` and `git`.
- Codex CLI, installed and logged in (`codex login`), with access to the review model. The default model is `gpt-6-astra`. Set `ASPERA_MODEL` to use another one.
- `gh`, only if you review pull requests.

## Install

Tell your agent: "Install the Aspera skill from https://github.com/Swader/aspera." The agent should do these steps.

1. Clone the repo into its skills folder, in a folder named `aspera`:

   | Agent | Folder |
   | --- | --- |
   | Cursor | `~/.cursor/skills/aspera` |
   | Codex | `~/.codex/skills/aspera` |
   | Claude Code | `~/.claude/skills/aspera` |

   ```bash
   git clone https://github.com/Swader/aspera.git ~/.cursor/skills/aspera
   ```

2. Fix the paths in `SKILL.md`. It assumes the Cursor folder and Cursor's `AwaitShell` tool. In another folder or agent, change the script path in step 3. In another agent, also use that agent's own way to wait for a background command.
3. Find the Codex binary with `command -v codex`. Codex can be installed somewhere else, for example in a global npm folder, under Homebrew, or inside an app bundle. If it is not on `PATH`, add its folder to `PATH`, or put the full path in the two places where `scripts/aspera.sh` calls `codex`. Adjust any other path that does not match the machine.
4. Check the install with `bash -n scripts/aspera.sh` and `codex --version`. Do not run a real review as a smoke test, because an `xhigh` review takes 10 to 40 minutes.

## Use

- `/aspera` reviews the file most recently created or edited in the chat. If there is no such file, it reviews the last substantive answer.
- `/aspera <file, PR URL or text>` reviews that target.

Each run writes `review.md` and `codex.log` to `~/.cursor/aspera/<timestamp>-<name>/`. Codex keeps the session, so you can continue the review with `codex resume`.

| Variable | Default |
| --- | --- |
| `ASPERA_MODEL` | `gpt-6-astra` |
| `ASPERA_EFFORT` | `xhigh` |
| `ASPERA_OUT_DIR` | `~/.cursor/aspera` |

## Safety

The script runs Codex with `-s danger-full-access`, which gives it full file and network access. The prompt tells Astra not to edit, commit or switch branches in your checkouts, and never to print secret values. The prompt also lets Astra use credentials from its Codex `local.env` and from env files in folders it reads, and lets it use computer and browser control. If you do not want this, edit the prompt in `scripts/aspera.sh` before you use the skill.
