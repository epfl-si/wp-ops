#!/usr/bin/env bash
#Petit script pour la moyenne, médiane et du 95e percentil en bash d'un fichier de mesure de ratio wp-cli/task

echo -e "
zstats_ratio.sh  zf201006.1019 \n"

#test si l'argument est vide
if [ -z "$1" ]
  then
    echo -e "\nUsage:
zstats_ratio.sh toto.txt
"
    exit
fi

echo -e "Moyenne: \c"
cat $1 | grep 'zratio_duration_wp_task' | awk '{print $2}' | sort -n | awk '{ sum += $1; n++ } END { if (n > 0) print sum / n; }' 

echo -e "Médiane: \c"
cat $1 | grep 'zratio_duration_wp_task' | awk '{print $2}' | sort -n | awk '{count[NR] = $1;} END {if (NR % 2) {print count[(NR + 1) / 2];} else {print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0;}}' 

echo -e "95e percentil: \c"
cat $1 | grep 'zratio_duration_wp_task' | awk '{print $2}' | sort -n | awk 'BEGIN{c=0} length($0){a[c]=$0;c++}END{p5=(c/100*5); p5=p5%1?int(p5)+1:p5; print a[c-p5-1]}' 

echo ""

