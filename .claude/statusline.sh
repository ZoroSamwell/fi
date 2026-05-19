#!/usr/bin/env bash
input=$(cat)
cwd=$(echo "$input" | jq -r '.workspace.current_dir // empty')
model=$(echo "$input" | jq -r '.model.display_name // empty')
remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')

parts=()
[ -n "$cwd" ] && parts+=("$cwd")
[ -n "$model" ] && parts+=("$model")
[ -n "$remaining" ] && parts+=("Context: ${remaining}% remaining")

printf '%s' "$(IFS=' | '; echo "${parts[*]}")"
