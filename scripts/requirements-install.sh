#!/bin/bash

docker run --rm -it \
    -w /code \
    -v $(pwd):/code \
    -v $(pwd)/.python-venv:/opt/venv/ \
    python:3.8-slim \
    bash -c 'find . -name "requirements.txt" -exec pip install -t /opt/venv/ -r {} \;'
