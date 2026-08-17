#!/usr/bin/env bash
# Bumps the version in pyproject.toml, commits, tags, and pushes.
# Pushing the tag triggers .github/workflows/python-publish.yml, which
# builds the package, creates a GitHub release, and publishes to PyPI.
#
# Usage: scripts/release.sh [patch|minor|major]   (default: patch)
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

BUMP="${1:-patch}"
case "$BUMP" in
  patch|minor|major) ;;
  *) echo "Usage: $0 [patch|minor|major]" >&2; exit 1 ;;
esac

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is not clean. Commit or stash changes first." >&2
  exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" != "main" ]]; then
  echo "Refusing to release from branch '$BRANCH' (expected 'main')." >&2
  exit 1
fi

git fetch origin main
if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]]; then
  echo "Local main is not in sync with origin/main. Pull/push first." >&2
  exit 1
fi

CURRENT_VERSION="$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"

NEXT_VERSION="$(python3 - "$CURRENT_VERSION" "$BUMP" <<'PY'
import sys
version, bump = sys.argv[1], sys.argv[2]
major, minor, patch = (int(p) for p in version.split("."))
if bump == "major":
    major, minor, patch = major + 1, 0, 0
elif bump == "minor":
    minor, patch = minor + 1, 0
else:
    patch += 1
print(f"{major}.{minor}.{patch}")
PY
)"

echo "Releasing ${CURRENT_VERSION} -> ${NEXT_VERSION}"
read -r -p "Continue? [y/N] " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "Aborted."
  exit 1
fi

sed -i "s/^version = \"${CURRENT_VERSION}\"/version = \"${NEXT_VERSION}\"/" pyproject.toml

git add pyproject.toml
git commit -m "Release ${NEXT_VERSION}"
git tag -a "${NEXT_VERSION}" -m "Release ${NEXT_VERSION}"

git push origin main
git push origin "${NEXT_VERSION}"

echo ""
echo "Pushed tag ${NEXT_VERSION}. Build/release/PyPI publish now running in GitHub Actions:"
echo "  https://github.com/danruggi/ispider/actions"
