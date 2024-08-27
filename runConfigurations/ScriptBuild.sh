#!/bin/bash
echo "Running this needs a lot of setup (not just flet). Please check flet documentation if anything fails."

rm -rf build
source .venv/bin/activate
mkdir -p build_tmp
mkdir -p builds/linux
mkdir -p builds/web
mkdir -p builds/android

flet build linux -o build_tmp
mv build_tmp/* builds/linux

flet publish main.py -a assets --app-name "Citynav München" --base-url / --distpath build_tmp
mv build_tmp/* builds/web

flet build apk -o build_tmp
mv build_tmp/* builds/android

rm -rf build_tmp

echo "Done"