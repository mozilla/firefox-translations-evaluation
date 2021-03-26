# Bergamot Evaluation

Calculates BLEU scores for [bergamot-translator](https://github.com/mozilla/bergamot-translator) and compares to other translation systems.


## Clone repo

```
mkdir workspace

cd workspace

git clone https://github.com/mozilla/bergamot-evaluation.git

cd bergamot-evaluation

```

## Docker based build
Recommended memory size for Docker is **8gb**.

Marian compilation requires quite a lot of memory per job.
You can monitor the amount of memory with `docker stats` and if it is not enough, 
either increase it in docker resources or limit number of jobs in `make` command
of [bergamot-translator](install/install-bergamot-translator.sh) and
[marian](install/install-marian.sh) installation scripts.
For example
`make -j4`


## Start docker

Specify local workspace directory:

`export LOCAL_WORKSPACE=<absolute path to local directory>`

Specify Azure key and location if you want to add Azure Translator API for comparison:

`export AZURE_TRANSLATOR_KEY=<Azure translator resource API key>`

`export AZURE_LOCATION=<location>` - optional, specify if it's different than default `global`

Specify GCP credentials json path if you want to add Google Translator API for comparison:

`export GCP_CREDS_PATH=<absolute path to .json>`

Build and run docker container:

`bash start_docker.sh`

## Run all

To install all at once and run evaluation with maximum available options,

from inside docker container run:

`bash run_all.sh`


## Installation scripts

You can run them separately if you need only some translators to be installed

`install/install-bergamot-translator.sh` clones and compiles [bergamot-translator](https://github.com/mozilla/bergamot-translator)

`install/install-marian.sh` clones and compiles [marian](https://github.com/marian-nmt/marian-dev)

`install/download-models.sh` downloads current Mozilla production [models](https://github.com/mozilla-applied-ml/bergamot-models/prod)



## Evaluation

From inside docker container run:


`python3 eval/evaluate.py --translators=bergamot,microsoft --pairs=all`

or 

`python3 eval/evaluate.py --help` for more options

### Translators

1. **bergamot** - uses compiled  [bergamot-translator](https://github.com/mozilla/bergamot-translator) 
2. **marian** - uses compiled [marian](https://github.com/marian-nmt/marian-dev)
3. **google** - users Google Translation [API](https://cloud.google.com/translate)
4. **microsoft** - users Azure Cognitive Services Translator [API](https://azure.microsoft.com/en-us/services/cognitive-services/translator/)

### Reuse already calculated scores

Use `--skip-existing` option to reuse already calculated scores saved as `results/xx-xx/*.bleu` files.
It is useful to continue evaluation if it was interrupted 
or to rebuild a full report reevaluating only selected translators.

### Datasets

Only official `wmtXX` datasets are supported at this point.

### Language pairs

With option `--pairs=all`, language pairs will be discovered 
from downloaded Mozilla production [models](https://github.com/mozilla-applied-ml/bergamot-models/prod) 
and evaluation will run for all of them.


## Results

See results reports [here](results/results.md).

Intermediate results and translations are be written to `results/xx-xx` folders.