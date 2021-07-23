#!/bin/bash


set -e
set -o pipefail

# clean SacreBLEU cache constantly to prevent error
# "This could be a problem with your system output or with sacreBLEU's reference database"
test -e /root/.sacrebleu && rm -r /root/.sacrebleu

sacrebleu -t "$DATASET" -l "$SRC-$TRG" --echo src \
    | tee "$EVAL_PREFIX.$SRC" \
    | $TRANSLATOR_CMD \
    | tee "$EVAL_PREFIX.$TRANSLATOR.$TRG" \
    | sacrebleu --score-only -q -t "$DATASET" -l "$SRC-$TRG" \
    | tee "$EVAL_PREFIX.$TRANSLATOR.$TRG.bleu"
