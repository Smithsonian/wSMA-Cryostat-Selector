#!/bin/bash
source $HOME/miniconda3/etc/profile.d/conda.sh
micromamba activate compressor # change to your conda environment's name
# -u: unbuffered output
python -u $HOME/.config/systemd/user/compressor-smax-daemon/lakeshore-smax-daemon.py
