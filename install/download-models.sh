#!/bin/bash

set -e

cd ..

if [ -e "bergamot-models" ]; then
    echo "Already cloned"
else
    echo "Cloning https://github.com/mozilla-applied-ml/bergamot-models.git"
    git clone https://github.com/mozilla-applied-ml/bergamot-models.git
fi

cd bergamot-models/prod

echo "Extracting models"
gzip -d -r *