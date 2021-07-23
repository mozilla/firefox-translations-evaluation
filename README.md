# Firefox Translations Evaluation
Calculates BLEU scores for Firefox Translations [models](https://github.com/mozilla/firefox-translations-models) 
using [bergamot-translator](https://github.com/mozilla/bergamot-translator) and compares them to other translation systems.

##Running

### Clone repo
```
git clone https://github.com/mozilla/firefox-translations-evaluation.git
cd firefox-translations-evaluation
```

### Start docker
Recommended memory size for Docker is **8gb**.

Specify a directory with [models](https://github.com/mozilla/firefox-translations-models):

`export MODELS=<absolute path to a local directory with models>`

Specify Azure key and location if you want to add Azure Translator API for comparison:

`export AZURE_TRANSLATOR_KEY=<Azure translator resource API key>`

`export AZURE_LOCATION=<location>` - optional, specify if it's different than default `global`

Specify GCP credentials json path if you want to add Google Translator API for comparison:

`export GCP_CREDS_PATH=<absolute path to .json>`

Build and run docker container:

`bash start_docker.sh`

On completion, your terminal should be attached to the launched container.

### Run evaluation
From inside docker container run:
```
python3 eval/evaluate.py --translators=bergamot,microsoft,google --pairs=all --skip-existing
--models-dir=/models/models/prod --results-dir=/models/evaluation/prod
```
more options:
```
python3 eval/evaluate.py --help
```

## Details
### Installation scripts
`install/install-bergamot-translator.sh` clones and compiles [bergamot-translator](https://github.com/mozilla/bergamot-translator)

`install/install-marian.sh` clones and compiles [marian](https://github.com/marian-nmt/marian-dev)

`install/download-models.sh` downloads current Mozilla production [models](https://github.com/mozilla/firefox-translations-models)

### Translators
1. **bergamot** - uses compiled [bergamot-translator](https://github.com/mozilla/bergamot-translator) in wasm mode
2. **marian** - uses compiled [marian](https://github.com/marian-nmt/marian-dev)
3. **google** - users Google Translation [API](https://cloud.google.com/translate)
4. **microsoft** - users Azure Cognitive Services Translator [API](https://azure.microsoft.com/en-us/services/cognitive-services/translator/)

### Reuse already calculated scores
Use `--skip-existing` option to reuse already calculated scores saved as `results/xx-xx/*.bleu` files.
It is useful to continue evaluation if it was interrupted 
or to rebuild a full report reevaluating only selected translators.

### Datasets
Only [SacreBLEU]() datasets are supported at the moment. 
All available datasets for a language pair are used for evaluation.

### Language pairs
With option `--pairs=all`, language pairs will be discovered 
in the specified models folder (option `--models-dir`) 
and evaluation will run for all of them.

### Results
Results will be written to the specified directory (option `--results-dir`).

Evaluation results for models that are used in Firefox Translation can be found in [firefox-translations-models/evaluation](https://github.com/mozilla/firefox-translations-models/tree/main/evaluation)
