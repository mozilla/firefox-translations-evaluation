#!/bin/bash


set -e
set -o pipefail

mkdir -p $EVAL_DIR
mkdir -p $EVAL_DIR/$SRC-$TRG

sacrebleu -t $DATASET -l $SRC-$TRG --echo src \
    | tee $EVAL_DIR/$SRC-$TRG/$DATASET.$SRC \
    | $TRANSLATOR_CMD \
    | tee $EVAL_DIR/$SRC-$TRG/$DATASET.$TRANSLATOR.$TRG \
    | sacrebleu --score-only -q -t $DATASET -l $SRC-$TRG \
    | tee $EVAL_DIR/$SRC-$TRG/$DATASET.$TRANSLATOR.$TRG.bleu