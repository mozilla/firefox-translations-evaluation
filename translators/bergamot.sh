#!/bin/bash

SRCVOCAB=$(find "${MODEL_DIR}" -name "srcvocab.*.spm")
TRGVOCAB=$(find "${MODEL_DIR}" -name "trgvocab.*.spm")
VOCAB=$(find "${MODEL_DIR}" -name "vocab.*.spm")
MODEL=$(find "${MODEL_DIR}" -name "model.${SRC}${TRG}.*.bin")
SHORTLIST=$(find "${MODEL_DIR}" -name "*${SRC}${TRG}.s2t.bin")
CONFIG="/tmp/bergamot.config.${SRC}${TRG}.yml"

cp translators/bergamot.config.yml "${CONFIG}"
sed -i -e "s+MODEL+${MODEL}+g" "${CONFIG}"
sed -i -e "s+SRCVOCAB+${SRCVOCAB:-$VOCAB}+g" "${CONFIG}"
sed -i -e "s+TRGVOCAB+${TRGVOCAB:-$VOCAB}+g" "${CONFIG}"
sed -i -e "s+SHORTLIST+${SHORTLIST}+g" "${CONFIG}"

$APP_PATH --model-config-paths "${CONFIG}" --log-level=info 2> errors.txt
