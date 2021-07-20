#!/bin/bash

set -e

cd ..

if [ -e "firefox-translations-models" ]; then
    echo "Already cloned"
else
    echo "Cloning https://github.com/mozilla/firefox-translations-models.git"
    git clone https://github.com/mozilla/firefox-translations-models.git
fi

cd firefox-translations-models

echo "Extracting models"
gzip -dr models/*
