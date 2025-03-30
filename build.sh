#!/bin/bash
python3 -m venv .venv
source .venv/bin/activate
which pip
which python
pip install -r requirements.txt --upgrade
pyinstaller --onefile main.py --add-data "./ssl/*:ssl/" --add-data "information.txt:." -n ServerAI_bin_ubuntu
