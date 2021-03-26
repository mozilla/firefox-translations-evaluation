#!/bin/bash

VOCAB=$(echo vocab.*.spm)
MODEL=$(echo *.bin)

ARGS=(
    -m $MODEL_DIR/$MODEL # Path to model file.
    --vocabs
        $MODEL_DIR/$VOCAB # source-vocabulary
        $MODEL_DIR/$VOCAB # target-vocabulary

    # The following increases speed through one-best-decoding, shortlist and quantization.
    --beam-size 1 --skip-cost --shortlist $MODEL_DIR/lex.$SRC$TRG.s2t 50 50 --int8shiftAlphaAll

    # Number of CPU threads (workers to launch). Parallelizes over cores and improves speed.
    # A value of 0 allows a path with no worker thread-launches and a single-thread.
    --cpu-threads 4

    # Maximum size of a sentence allowed. If a sentence is above this length,
    # it's broken into pieces of less than or equal to this size.
    --max-length-break 1024

    # Maximum number of tokens that can be fit in a batch. The optimal value
    # for the parameter is dependant on hardware and can be obtained by running
    # with variations and benchmarking.
    --mini-batch-words 1024

    # Three modes are supported
    #   - sentence: One sentence per line
    #   - paragraph: One paragraph per line.
    #   - wrapped_text: Paragraphs are separated by empty line.
    --ssplit-mode paragraph

    --quiet-translation
    --quiet
)

$BERGAMOT_APP_DIR/translate "${ARGS[@]}" $@
