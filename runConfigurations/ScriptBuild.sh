#!/bin/bash
echo "Running this needs a lot of setup (not just flet). Please check flet and makeself documentation if anything fails."

rm -rf build
source .venv/bin/activate
mkdir -p build_tmp/work

cp *.py build_tmp/
cp requirements.txt build_tmp/
cp -r assets build_tmp
cd build_tmp || exit

if [ -z "$1" ] || [ "$1" == "linux" ]
then
  mkdir -p builds/linux
  flet build linux --exclude "__pypackages__" -o work
  mv work/build_tmp work/de.mfxbe.Citynav
  makeself --nox11 work citynav-linux.run " and starting Citynav München ..." ./de.mfxbe.Citynav
  mv citynav-linux.run ../builds/linux/
  rm -rf work/*
fi

if [ -z "$1" ] || [ "$1" == "web" ]
then
  mkdir -p builds/web
  flet publish main.py -a assets --app-name "Citynav München" --base-url / --distpath work
  mv work/* ../builds/web
  rm ../builds/web/icons/*
  rm ../builds/web/favicon.png
  cp ../builds/web/icon.png ../builds/web/icons/icon.png
  cp ../builds/web/splash.png ../builds/web/icons/loading-animation.png
  cp ../builds/web/icon.png ../builds/web/favicon.png
fi

if [ -z "$1" ] || [ "$1" == "android" ]
then
  mkdir -p builds/android
  flet build apk --project Citynav --product "Citynav München" --org "de.mfxbe" --exclude "__pypackages__" -o work
  mv work/* ../builds/android
fi

cd .. || exit
rm -rf build_tmp

echo "Done"