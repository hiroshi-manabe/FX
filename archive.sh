#!/usr/bin/env bash
# archive.sh  --  produce two zip files the same way every time.
set -e

CODE_ZIP="fx_code_$(git rev-parse --short HEAD).zip"
DATA_ZIP="fx_sample_data.zip"

# Code & configs (no data, no build artefacts)
git archive --format=zip --output="$CODE_ZIP" --prefix=fx/ HEAD

# Data
zip -r "$DATA_ZIP" data/

echo "Created $CODE_ZIP and $DATA_ZIP"
