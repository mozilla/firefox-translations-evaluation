#!/bin/bash

VOCAB=$(echo $MODEL_DIR/vocab.*.spm)
MODEL=$(echo $MODEL_DIR/model.$SRC$TRG.intgemm.alphas.bin)

# These Marian options are set according to
# https://github.com/mozilla-extensions/bergamot-browser-extension/blob/main/src/core/static/wasm/bergamot-translator-worker.appendix.js#L36
# to imitate production setting

ARGS=(
    -m $MODEL
    --vocabs
        $VOCAB # source-vocabulary
        $VOCAB # target-vocabulary
    --beam-size 1
    --normalize 1.0
    --word-penalty 0
    # this setting is not supported
    # --max-length-break 128
    --mini-batch-words 1024
    --workspace 128
    --max-length-factor 2.0
    --skip-cost
    # cannot use GPU, this is CPU Marian build
    # --cpu-threads 0
    --cpu-threads 4
    --quiet
    --quiet-translation
    --shortlist $MODEL_DIR/lex.50.50.$SRC$TRG.s2t.bin 50 50
)

$APP_PATH "${ARGS[@]}" $@
