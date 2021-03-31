#!/bin/bash

#LOCAL_WORKSPACE=
#GCP_CREDS_PATH=
#AZURE_TRANSLATOR_KEY=


set -e

echo "Building docker image"
docker build -t bergamot-eval .

echo "Running docker container"
docker run --name bergamot-eval -it \
      -v $LOCAL_WORKSPACE:/workspace \
      -v $GCP_CREDS_PATH:/.gcp_creds \
      -e GOOGLE_APPLICATION_CREDENTIALS=/.gcp_creds \
      -e AZURE_TRANSLATOR_KEY=${AZURE_TRANSLATOR_KEY} \
      bergamot-eval
