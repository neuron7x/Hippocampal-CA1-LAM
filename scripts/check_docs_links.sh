#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

mode=${1:-local}
case "$mode" in
    local) flags=(--offline --include-fragments) ;;
    external) flags=(--exclude-all-private --accept '200..=299' --max-retries 2 --timeout 20
                      --host-concurrency 1 --host-request-interval 1s) ;;
    *) echo "Expected local or external, got $mode" >&2; exit 2 ;;
esac

scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
curl -fsSLo "$scratch/lychee.tar.gz" \
    https://github.com/lycheeverse/lychee/releases/download/lychee-v0.24.2/lychee-x86_64-unknown-linux-gnu.tar.gz
echo "1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a  $scratch/lychee.tar.gz" |
    sha256sum -c -
tar -xzf "$scratch/lychee.tar.gz" -C "$scratch" --strip-components=1 \
    lychee-x86_64-unknown-linux-gnu/lychee

git ls-files -z -- '*.md' > "$scratch/files"
mapfile -d '' -t files < "$scratch/files"
if (( ${#files[@]} == 0 )); then
    echo 'No tracked Markdown documents found' >&2
    exit 1
fi

"$scratch/lychee" --no-progress --config /dev/null --root-dir "$PWD" "${flags[@]}" -- "${files[@]}"
