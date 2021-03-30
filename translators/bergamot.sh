#!/bin/bash

VOCAB=$(echo vocab.*.spm)
MODEL=$(echo *.bin)

# These Marian options are set according to
# https://github.com/mozilla-extensions/bergamot-browser-extension/blob/main/src/core/static/wasm/bergamot-translator-worker.appendix.js#L36
# to imitate production setting

ARGS=(
    -m $MODEL_DIR/$MODEL
    --vocabs
        $MODEL_DIR/$VOCAB # source-vocabulary
        $MODEL_DIR/$VOCAB # target-vocabulary
    --beam-size 1
    --normalize 1.0
    --word-penalty 0
    --max-length-break 128
    --mini-batch-words 1024
    --workspace 128
    --max-length-factor 2.0
    --skip-cost
    --cpu-threads 0
    --quiet
    --quiet-translation
    --shortlist $MODEL_DIR/lex.$SRC$TRG.s2t 50 50
)

$APP_PATH "${ARGS[@]}" $@
