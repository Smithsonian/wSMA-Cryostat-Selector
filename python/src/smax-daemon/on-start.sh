#!/bin/bash
source $HOME/.bashrc
micromamba activate selector # change to your conda environment's name
# -u: unbuffered output
python -u $HOME/.config/systemd/user/selector-smax-daemon/selector-smax-daemon.py
