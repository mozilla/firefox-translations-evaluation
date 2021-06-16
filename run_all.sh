#!/bin/bash

set -e

echo "Installing translators"
bash ./install/insall-bergamot-translator.sh
bash ./install/insall-marian.sh
bash ./install/download-models.sh

chmod +x eval.sh
chmod +x translators/bergamot.sh
chmod +x translators/marian.sh

echo "Running evaluation"
python3 eval/evaluate.py --translators=bergamot,marian,google,microsoft --pairs=all --skip-existing --envs=prod,dev
