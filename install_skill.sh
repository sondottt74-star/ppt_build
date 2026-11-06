#!/usr/bin/env bash
# Install / update the paper-ppt skill from this repo into Cursor, Claude Code and Codex skill folders.
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
for dest in "$HOME/.cursor/skills" "$HOME/.claude/skills" "$HOME/.codex/skills"; do
  mkdir -p "$dest"
  rm -rf "$dest/paper-ppt"
  cp -R "$REPO/skill/paper-ppt" "$dest/paper-ppt"
  if [ "$REPO" != "$HOME/research/ppt_build" ]; then
    sed -i '' "s#~/research/ppt_build#$REPO#g" "$dest/paper-ppt/SKILL.md"
  fi
  echo "installed $dest/paper-ppt"
done
