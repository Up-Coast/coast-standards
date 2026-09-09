#!/bin/sh
# Build the documentation site.
#
# The rules and guides are read in three places — this repository, an adopting project,
# and the release tarball — so they are never moved or copied into a docs/ tree of their
# own. MkDocs will not take the repository root as its docs_dir, so this stages the pages
# into a scratch directory with their paths UNCHANGED, which is what keeps a relative link
# like `rules/00-priority-rules.md` working on GitHub and on the site alike.
#
# The staging directory is rebuilt from scratch every run and is not committed.
#
# Usage:  tools/build-docs.sh          build into site/
#         tools/build-docs.sh serve    build and serve locally on :8000
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"

staging=.docs-build
rm -rf "$staging"
mkdir -p "$staging"

# The pages the nav names, staged at the same relative paths.
for path in README.md CONTRIBUTING.md LICENSE.md CHANGELOG.md TEMPLATE-CLAUDE.md skills docs rules enforcement; do
    [ -e "$path" ] || { echo "build-docs: missing $path" >&2; exit 1; }
    mkdir -p "$staging/$(dirname "$path")"
    cp -R "$path" "$staging/$(dirname "$path")/"
done

# enforcement/ carries the implementation as well as its documents; the site wants only
# the documents, and leaving the code out keeps the search index about the rules.
find "$staging/enforcement" -type f ! -name '*.md' -delete
find "$staging/enforcement" -type d -empty -delete

if [ "${1:-build}" = "serve" ]; then
    exec mkdocs serve
fi
mkdocs build --strict
echo "built: $root/site"
