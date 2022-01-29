#!/bin/bash

VOCAB=$(echo "${MODEL_DIR}"/vocab.*.spm)
MODEL="${MODEL_DIR}/model.${SRC}${TRG}.intgemm.alphas.bin"
SHORTLIST="${MODEL_DIR}/lex.50.50.${SRC}${TRG}.s2t.bin"
CONFIG="/tmp/bergamot.config.${SRC}${TRG}.yml"

cp translators/bergamot.config.yml "${CONFIG}"
sed -i -e "s+MODEL+${MODEL}+g" "${CONFIG}"
sed -i -e "s+VOCAB+${VOCAB}+g" "${CONFIG}"
sed -i -e "s+SHORTLIST+${SHORTLIST}+g" "${CONFIG}"

$APP_PATH --model-config-paths "${CONFIG}"
