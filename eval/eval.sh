#!/bin/bash


set -e
set -o pipefail

sacrebleu -t "$DATASET" -l "$SRC-$TRG" --echo src \
    | tee "$EVAL_PREFIX.$SRC" \
    | $TRANSLATOR_CMD \
    | tee "$EVAL_PREFIX.$TRANSLATOR.$TRG" \
    | sacrebleu --score-only -q -t "$DATASET" -l "$SRC-$TRG" \
    | tee "$EVAL_PREFIX.$TRANSLATOR.$TRG.bleu"
