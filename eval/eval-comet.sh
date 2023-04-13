#!/bin/bash


set -e
set -o pipefail

mkdir -p $(dirname "${EVAL_PREFIX}")

sacrebleu -t "$DATASET" -l "$SRC-$TRG" --echo src \
    | tee "$EVAL_PREFIX.$SRC" \
    | $TRANSLATOR_CMD \
    | tee "$EVAL_PREFIX.$TRANSLATOR.$TRG" \
    ; comet-score --gpus "$GPUS" --quiet -d "$DATASET:$SRC-$TRG" -t "$EVAL_PREFIX.$TRANSLATOR.$TRG" \
    | tee "$EVAL_PREFIX.$TRANSLATOR.$TRG.comet"
