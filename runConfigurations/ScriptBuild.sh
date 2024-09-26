#!/bin/bash
echo "Running this needs a lot of setup (not just flet). Please check flet and makeself documentation if anything fails."

rm -rf build
source .venv/bin/activate
mkdir -p build_tmp/work

cp *.py build_tmp/
cp -r custom build_tmp/custom
cp requirements.txt build_tmp/
cp -r assets build_tmp
cd build_tmp || exit

if [ -z "$1" ] || [ "$1" == "linux" ]
then
  rm -rf ../builds/linux || true
  mkdir -p ../builds/linux
  flet build linux --exclude "__pypackages__" -o work
  mv work/build_tmp work/de.mfxbe.Citynav
  makeself --nox11 work citynav-linux.run " and starting Citynav München ..." ./de.mfxbe.Citynav
  mv citynav-linux.run ../builds/linux/
  rm -rf work/*
fi

if [ -z "$1" ] || [ "$1" == "web" ]
then
  rm -rf ../builds/web || true
  mkdir -p ../builds/web
  flet publish main.py -a assets --app-name "Citynav München" --base-url "/$2" --distpath work
  mv work/* ../builds/web
  rm ../builds/web/icons/*
  rm ../builds/web/favicon.png
  cp ../builds/web/icon.png ../builds/web/icons/icon.png
  cp ../builds/web/splash.png ../builds/web/icons/loading-animation.png
  cp ../builds/web/icon.png ../builds/web/favicon.png
  cp ../web_manifest.json ../builds/web/manifest.json
  sed -i -e 's/black/#36618e/g' ../builds/web/index.html
  sed -i -e 's/apple-touch-icon-192/icon/g' ../builds/web/index.html
fi

if [ -z "$1" ] || [ "$1" == "android" ]
then
  rm -rf ../builds/android || true
  mkdir -p ../builds/android
  flet build apk --project Citynav --product "Citynav München" --org "de.mfxbe" --exclude "__pypackages__" -o work
  mv work/* ../builds/android
fi

cd .. || exit
rm -rf build_tmp

echo "Done"