#!/bin/bash
echo "Running this needs a lot of setup (not just flet). Please check flet documentation if anything fails."

rm -rf build
source .venv/bin/activate
mkdir -p build_tmp/work
mkdir -p builds/linux
mkdir -p builds/web
mkdir -p builds/android

cp *.py build_tmp/
cp requirements.txt build_tmp/
cp -r assets build_tmp
cd build_tmp || exit

flet build linux --exclude "__pypackages__" -o work
makeself --nox11 work citynav-linux.run "and starting Citynav München ..." ./build_tmp
mv citynav-linux.run ../builds/linux/
rm -rf work/*

flet publish main.py -a assets --app-name "Citynav München" --base-url / --distpath work
mv work/* ../builds/web
rm ../builds/web/icons/*
rm ../builds/web/favicon.png
cp ../builds/web/icon.png ../builds/web/icons/icon.png
cp ../builds/web/splash.png ../builds/web/icons/loading-animation.png
cp ../builds/web/icon.png ../builds/web/favicon.png


flet build apk --project Citynav --product "Citynav München" --org "de.mfxbe" --exclude "__pypackages__" -o work -vv
mv work/* ../builds/android

cd .. || exit
rm -rf build_tmp

echo "Done"