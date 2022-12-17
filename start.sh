#!/bin/bash

cd /home/pi/projects/parafia-szopka
d=$(pwd)
echo Directory $d
echo Path $PATH

/home/pi/.local/bin/pipenv run python szopka_na_monety.py
echo Done.
