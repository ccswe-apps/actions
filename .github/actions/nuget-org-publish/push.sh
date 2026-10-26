#!/usr/bin/env bash
# Pushes nupkg/*.nupkg (and each matching .snupkg) to nuget.org with the Trusted Publishing key.
set -euo pipefail

dotnet nuget push "nupkg/*.nupkg" --source https://api.nuget.org/v3/index.json \
  --api-key "$NUGET_API_KEY" --skip-duplicate
