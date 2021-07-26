#!/bin/bash

set -e

if [ -e "firefox-translations-models" ]; then
    echo "Already cloned"
else
    echo "Cloning https://github.com/mozilla/firefox-translations-models.git"
    git clone https://github.com/mozilla/firefox-translations-models.git

    echo "Extracting models"
    gzip -dr firefox-translations-models/models/*
fi
