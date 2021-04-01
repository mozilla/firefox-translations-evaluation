#!/bin/bash

# Downloads and compiles Marian
#

set -e

cd ..

if [ -e "marian-dev" ]; then
    echo "already cloned"
else
    echo "Cloning https://github.com/browsermt/marian-dev"
    git clone https://github.com/browsermt/marian-dev
fi

echo "Compiling marian-dev"
mkdir -p marian-dev/build
cd marian-dev/build
cmake .. -DUSE_SENTENCEPIECE=on -DCOMPILE_CPU=on -DUSE_FBGEMM=on -DCOMPILE_CUDA=off
make -j$(nproc)
cd ../..
