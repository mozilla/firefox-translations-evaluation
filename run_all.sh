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
python3 eval/evaluate.py --translators=marian,bergamot,google,microsoft --pairs=all --skip-existing \
  --models-dir=firefox-translations-models/prod --results-dir=results/prod
python3 eval/evaluate.py --translators=marian,bergamot,google,microsoft --pairs=all --skip-existing \
  --models-dir=firefox-translations-models/dev --results-dir=results/dev
