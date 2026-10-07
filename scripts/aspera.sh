#!/usr/bin/env bash
# Send a target file to Astra (Codex CLI) for an adversarial review.
# Usage: aspera.sh --target <file> [--brief <file>] [--cd <dir>]
set -euo pipefail

fail() { # fail <code> <log> <message>
  echo "ASPERA_FAILED exit=$1 log=$2"
  echo "$3" >&2
  exit "$1"
}

abspath() { (cd "$(dirname "$1")" && printf '%s/%s\n' "$(pwd -P)" "$(basename "$1")"); }

target="" brief="" cd_dir=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) target="${2:-}"; shift 2 ;;
    --brief) brief="${2:-}"; shift 2 ;;
    --cd) cd_dir="${2:-}"; shift 2 ;;
    *) fail 2 none "Unknown argument: $1" ;;
  esac
done

[[ -n "$target" && -f "$target" ]] || fail 2 none "Target file missing: '${target}'"
target="$(abspath "$target")"
if [[ -n "$brief" ]]; then
  [[ -f "$brief" ]] || fail 2 none "Brief file missing: '$brief'"
  brief="$(abspath "$brief")"
fi
if [[ -z "$cd_dir" ]]; then
  cd_dir="$(git -C "$(dirname "$target")" rev-parse --show-toplevel 2>/dev/null || dirname "$target")"
fi
[[ -d "$cd_dir" ]] || fail 2 none "Working directory missing: '$cd_dir'"

run_dir="${ASPERA_OUT_DIR:-$HOME/.cursor/aspera}/$(date +%Y%m%d-%H%M%S)-$(basename "$target")"
mkdir -p "$run_dir"
review="$run_dir/review.md"
log="$run_dir/codex.log"
echo "ASPERA_STARTED review=$review log=$log"

command -v codex >/dev/null 2>&1 || fail 127 "$log" "codex is not on PATH"

prompt="$(cat <<'EOF'
Adversarially review this plan for simplicity in code, maximality in functionality, and minimalism in tech debt. Review it from different perspectives and personas, and respond with suggested improvements, if any.
Go greybeard: we don't solve problems by throwing compute at them; we're not Node.js script kids. Cache is king, parallelism exists for a reason, queues should be non-blocking and async, and other practices that have proven themselves at scale apply. If there is a clear but radical opportunity to gain a 10x improvement in performance or cost, propose it.
Ground your opinions and speculations in the truth of code. If the plan touches on code related to a different repo, switch context into an existing local checkout of said code as needed, look through it thoroughly, and come back with facts, not speculations. Use any tools at your disposal to be thorough - your local.env as well as the env file in any folder you look at should both have useful credentials for accessing any SaaS which might provide you with extra information, and for everything else there is computer use and browser use, both of which you are fully permitted to utilize to the maximum of their potential to reach a useful conclusion.
EOF
)"
prompt+=$'\n\n'"Target: $target"
[[ -n "$brief" ]] && prompt+=$'\n'"Context brief: $brief"
prompt+=$'\n'"Read the target and the context brief (if given) first."
prompt+=$'\n'"This is a review: do not edit, commit, or change branches in any checkout the user works in. To read another revision, use git show, git fetch, or a temporary git worktree under /tmp."
prompt+=$'\n'"Never print secret values. End with a prioritized list of concrete improvements, each with file:line evidence."

rc=0
codex exec -m "${ASPERA_MODEL:-gpt-6-astra}" -c model_reasoning_effort="${ASPERA_EFFORT:-xhigh}" \
  -s danger-full-access -C "$cd_dir" --skip-git-repo-check -o "$review" - <<<"$prompt" >"$log" 2>&1 || rc=$?

if [[ $rc -eq 0 && ! -s "$review" ]]; then
  echo "codex exited 0 but wrote no review" >>"$log"
  rc=1
fi
if [[ $rc -ne 0 ]]; then
  echo "ASPERA_FAILED exit=$rc log=$log"
  tail -n 20 "$log"
  exit "$rc"
fi
echo "ASPERA_DONE $review"
