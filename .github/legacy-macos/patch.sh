#!/usr/bin/env bash
# Patches an upstream Craft App checkout so it builds for macOS 10.12 Sierra (Intel).
# Applied at build time only, so the fork's main can follow upstream with "Sync fork".
# Usage: .github/legacy-macos/patch.sh <github-owner-of-the-forks>
set -euo pipefail
OWNER="${1:?github owner}"
MIN=10.12
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# 1. Deployment target and the bundle's minimum system version.
perl -pi -e "s/^export MACOSX_DEPLOYMENT_TARGET=.*/export MACOSX_DEPLOYMENT_TARGET=$MIN/" packaging/macos/package.sh
grep -q "MACOSX_DEPLOYMENT_TARGET=$MIN" packaging/macos/package.sh
perl -0pi -e "s#(<key>LSMinimumSystemVersion</key>\s*<string>)[^<]*(</string>)#\${1}$MIN\${2}#" packaging/macos/Info.plist.in
grep -A1 LSMinimumSystemVersion packaging/macos/Info.plist.in | grep -q "$MIN"

# 2. The launcher installs and updates from the forks, never from the official 11.0+ builds.
if [ -f crates/core/src/catalog.rs ] && grep -q 'LAUNCHER_REPO' crates/core/src/catalog.rs; then
  perl -pi -e "s#\"storytold/#\"$OWNER/#g; s#(GITHUB_OWNER: &str = )\"storytold\"#\${1}\"$OWNER\"#" crates/core/src/catalog.rs
  grep -q "GITHUB_OWNER: &str = \"$OWNER\"" crates/core/src/catalog.rs
  # The ArtCraft release feed lists the official builds: skip it and ask GitHub directly.
  perl -0pi -e 's#\.unwrap_or_else\(\|\| artcraft_launcher_core::feed::FEED_URL\.to_string\(\)\)#.unwrap_or_default()#' crates/native/src/backend.rs
  perl -0pi -e 's#(fn fetch_feed\([^{]*\{\n)#${1}    if url.is_empty() {\n        return FeedFetch::Failed;\n    }\n#' crates/native/src/backend.rs
  grep -q 'unwrap_or_default()' crates/native/src/backend.rs
  grep -q 'if url.is_empty()' crates/native/src/backend.rs
fi
echo "patched for macOS $MIN (owner $OWNER)"
