#!/bin/bash

# to run locally
#MODELS=
#GCP_CREDS_PATH=
#AZURE_TRANSLATOR_KEY=


echo "Building docker image"
docker build -t bergamot-eval .

echo "Running docker container"
docker run --name bergamot-eval -it --shm-size=16gb --rm \
      --runtime=nvidia --gpus all \
      -v $MODELS:/models \
      -v $GCP_CREDS_PATH:/.gcp_creds \
      -e GOOGLE_APPLICATION_CREDENTIALS=/.gcp_creds \
      -e AZURE_TRANSLATOR_KEY=${AZURE_TRANSLATOR_KEY} \
      bergamot-eval
