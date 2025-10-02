#!/usr/bin/env bash
set -euo pipefail

# Run local secret scans, excluding .venv and other noisy paths.
# Reports are saved to output/security/.

mkdir -p output/security

# Gitleaks (filesystem, excluding git history). Gitleaks has been quiet even with .venv,
# but we run it for completeness.
if command -v gitleaks >/dev/null 2>&1; then
  echo "[security_scan] Running gitleaks (filesystem)" >&2
  gitleaks detect \
    --source . \
    --no-git \
    --redact \
    --report-format json \
    --report-path output/security/gitleaks.filesystem.json || true

  echo "[security_scan] Running gitleaks (git history)" >&2
  gitleaks detect \
    --source . \
    --redact \
    --report-format json \
    --report-path output/security/gitleaks.git.json || true
else
  echo "[security_scan] WARN: gitleaks not installed" >&2
fi

# TruffleHog (filesystem) with exclude list
if command -v trufflehog >/dev/null 2>&1; then
  echo "[security_scan] Running trufflehog (filesystem) with excludes" >&2
  trufflehog filesystem . \
    --exclude-paths scripts/trufflehog-exclude.txt \
    --json > output/security/trufflehog.filesystem.json || true

  echo "[security_scan] Running trufflehog (git)" >&2
  trufflehog git file://. \
    --json > output/security/trufflehog.git.json || true
else
  echo "[security_scan] WARN: trufflehog not installed" >&2
fi

echo "[security_scan] Complete. Reports in output/security" >&2
