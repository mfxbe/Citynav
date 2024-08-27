#!/bin/bash

#clean and setup
rm -rf assets/maps/
rm -f stopsdata.py
mkdir -p prepare_tmp
mkdir -p assets/maps/

#Get maps and convert to images
wget https://www.mvv-muenchen.de/fileadmin/mediapool/03-Plaene_Bahnhoefe/Netzplaene/Downloads_2024/2024_layout_SURTX_ZoneM_SCR.pdf -O prepare_tmp/lc.pdf
wget https://www.mvv-muenchen.de/fileadmin/mediapool/03-Plaene_Bahnhoefe/Netzplaene/Downloads_2024/2024_layout_SUR_gesamtnetz_SCR.pdf -O prepare_tmp/la.pdf
wget https://www.mvv-muenchen.de/fileadmin/mediapool/03-Plaene_Bahnhoefe/Netzplaene/Downloads_2024/A4-Nachtnetz-2024_SCREEN.pdf -O prepare_tmp/nc.pdf
wget https://www.mvv-muenchen.de/fileadmin/mediapool/03-Plaene_Bahnhoefe/VLP/Verkehrslinienplaene_Muenchen_und_Region/MVV_VLP_STADT_Muenchen.pdf -O prepare_tmp/mc.pdf
wget https://www.mvv-muenchen.de/fileadmin/mediapool/03-Plaene_Bahnhoefe/VLP/Verkehrslinienplaene_Muenchen_und_Region/MVV_VLP_Region.PDF -O prepare_tmp/ma.pdf

for file in prepare_tmp/*.pdf; do
    file=${file::-4}
    file=${file:12}
    pdftoppm -jpeg -r 300 "prepare_tmp/$file.pdf" > "prepare_tmp/$file.jpeg"
    rm -f "prepare_tmp/$file.pdf"
done

mv prepare_tmp/* assets/maps/

#Get stop data, parse and save as json string
wget https://www.mvv-muenchen.de/fileadmin/mediapool/02-Fahrplanauskunft/03-Downloads/openData/Haltestellen_Tarifzonen_Stand_231210.csv -O prepare_tmp/stops.csv
cat prepare_tmp/stops.csv | python -c 'import csv, json, sys; print(json.dumps([dict(r) for r in csv.DictReader(sys.stdin, delimiter=";")]))' > prepare_tmp/stops.json
stops=`cat prepare_tmp/stops.json`
touch stopsdata.py
printf "#!/usr/bin/python\nstops=\"\"\"$stops\"\"\"" > stopsdata.py

rm -rf prepare_tmp