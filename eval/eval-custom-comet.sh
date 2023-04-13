#!/bin/bash


set -e
set -o pipefail

$TRANSLATOR_CMD < "$EVAL_PREFIX.$SRC" \
  | tee "$EVAL_PREFIX.$TRANSLATOR.$TRG" \
  ; comet-score --quiet --gpus "$GPUS" -s "$EVAL_PREFIX.$SRC" -t "$EVAL_PREFIX.$TRANSLATOR.$TRG" -r "$EVAL_PREFIX.$TRG" \
  | tee "$EVAL_PREFIX.$TRANSLATOR.$TRG.comet"


