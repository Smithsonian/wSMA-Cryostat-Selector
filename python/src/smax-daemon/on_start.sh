#!/bin/bash
CONDA_PREFIX='/opt/mamba';
CONDA_ENV='selector';

eval "$CONDA_PREFIX/envs/$CONDA_ENV/bin/python selector_smax_daemon.py";
