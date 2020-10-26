#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Petit script pour parser les logs de Ansible (reclog) dans ce project
# version qui calcul la durée de chaque Task/Site !
# sources: https://janakiev.com/blog/python-shell-commands/
# sources: https://github.com/zuzu59/reclog

import signal
import sys
import os
import datetime

version = "parse-ansible-out5.py  zf201007.1737 "

"""
Version avec le parsing des logs wp-cli (zf201005.1408)

TODO:

- il faut sommer la durée du wp-cli quand il est utilisé plusieurs fois dans la même tâche/site !  zf201006.1129

- pourquoi il y a 860 'wp-media-folder options' dans les logs pour seulement 10x sites ? zf200707.1737

ATTENTION: il ne faut pas oublier, avant de lancer la *petite fusée* d'effacer le fichier de log de reclog !
rm /Users/zuzu/dev-zf/reclog/file.log

génération du fichier logs:
Le faire avec la petite fusée du template dans l'interface WEB de AWX !

usage:
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_x_sites_y_forks_z_pods.txt

*******************
Tests de charges avec le modèle 'align' des sites
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_10_sites_1_forks_1_pods.txt2
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_10_sites_5_forks_1_pods.txt2
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_10_sites_5_forks_1_pods_mitogen.txt2
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_10_sites_5_forks_1_pods_opcache.txt2
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_10_sites_5_forks_2_pods_parll.txt2
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_10_sites_5_forks_2_pods_cache.txt2
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_10_sites_10_forks_1_pods.txt2
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_10_sites_10_forks_1_pods_pipe.txt2
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_10_sites_10_forks_1_pods_debug4.txt2
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_10_sites_2_forks_5_pods.txt2
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_100_sites_30_forks_1_pods.txt2
cp /Users/zuzu/dev-zf/reclog/file.log awx_logs_align_100_sites_17_forks_3_pods.txt2


./parse-ansible-out4.py awx_logs_align_10_sites_1_forks_1_pods.txt > toto.txt
./parse-ansible-out5.py awx_logs_align_10_sites_5_forks_1_pods.txt > toto1.txt
./parse-ansible-out5.py awx_logs_align_10_sites_5_forks_1_pods_mitogen.txt > toto2.txt
./parse-ansible-out5.py awx_logs_align_10_sites_5_forks_1_pods_opcache.txt > toto3.txt
./parse-ansible-out4.py awx_logs_align_10_sites_5_forks_2_pods_parll.txt > toto.txt
./parse-ansible-out4.py awx_logs_align_10_sites_5_forks_2_pods_cache.txt > toto.txt
./parse-ansible-out4.py awx_logs_align_10_sites_10_forks_1_pods.txt > toto.txt
./parse-ansible-out4.py awx_logs_align_10_sites_10_forks_1_pods_pipe.txt > toto.txt
./parse-ansible-out4.py awx_logs_align_10_sites_10_forks_1_pods_debug4.txt > toto.txt
./parse-ansible-out4.py awx_logs_align_10_sites_2_forks_5_pods.txt > toto.txt
./parse-ansible-out5.py awx_logs_align_100_sites_30_forks_1_pods.txt > toto.txt
./parse-ansible-out4.py awx_logs_align_100_sites_17_forks_3_pods.txt > toto.txt

*******************
Tests avec seulement un site en local pour tester le nouveau parser avec wp-cli
cp /Users/zuzu/dev-zf/reclog/file.log local_logs_plugins_1x.txt

./parse-ansible-out5.py local_logs_plugins_1x.txt > toto.txt


Puis voir le résultat dans un browser
http://noc-tst.idev-fsd.ml:9092/


Pour mettre à zéro la 'table' dans InfluxDB
export zinfluxdb_table="awx_logs1"
curl -i -XPOST "$dbflux_srv_host:$dbflux_srv_port/query?u=$dbflux_u_admin&p=$dbflux_p_admin&db=$dbflux_db"  --data-urlencode "q=SHOW MEASUREMENTS"
curl -i -XPOST "$dbflux_srv_host:$dbflux_srv_port/query?u=$dbflux_u_admin&p=$dbflux_p_admin&db=$dbflux_db"  --data-urlencode "q=DROP MEASUREMENT $zinfluxdb_table"
curl -i -XPOST "$dbflux_srv_host:$dbflux_srv_port/query?u=$dbflux_u_admin&p=$dbflux_p_admin&db=$dbflux_db"  --data-urlencode "q=SHOW MEASUREMENTS"
"""


zloop_parse = 40000000
zloop_curl = 10000000
zloop_profiling = 10000000

# True False
zverbose_unix_time = False
zverbose_parsing = False
zverbose_duration = False
zverbose_dico = False
zverbose_curl = False
zverbose_grafana = False
zverbose_profiling = False

zmake_curl = False
zsend_grafana = False
zmake_profiling = True

zinfluxdb_table = "awx_logs1"

db_logs = {}
ztask_id = 0
ztask_line = 0
ztask_name = ""
ztask_pod = ""
ztask_path = ""
ztask_site_name = ""
ztask_site_id = 0
ztask_time = ""
ztask_duration = 0

ztask_time_1 = ""
ztask_time_obj_1 = ""
ztask_unix_time_1 = 0

ztask_time_2 = ""
ztask_time_obj_2 = ""
ztask_unix_time_2 = 0

# ALT+CMD+F bascule du code au terminal

# Structure du dictionnaire
# index: 1
#     task_name: toto1
#     task_path: tutu1
#     index: 1
#         site_name: tata1
#         time_start: 123
#         time_end: 234
#         time_duree: 12
#     index: 2
#         site_name: tata2
#         time_start: 345
#         time_end: 456
#         time_duree: 23
# index: 2
#     task_name: toto2
#     task_path: tutu2
#     index: 1
#         site_name: tata1
#         time_start: 123
#         time_end: 234
#         time_duree: 12
#     index: 2
#         site_name: tata2
#         time_start: 345
#         time_end: 456


def zprint_db_log():
    for i in range(1, len(db_logs)+1): 
        print("\n++++++++++++++++")
        print("ztask_name: " + str(i) + ", " + db_logs[i]["ztask_name"])
        print("ztask_path: " + db_logs[i]["ztask_path"])
        for j in range(1, (len(db_logs[i]) - 2) + 1):
            print("----")
            
            
            print("ztask_name: " + str(i) + ", " + db_logs[i]["ztask_name"])
            print("ztask_path: " + db_logs[i]["ztask_path"])


            print("ztask_site_name: " + str(j) + ", " + db_logs[i][j]["ztask_site_name"])
            print("ztask_pod: " + db_logs[i][j]["ztask_pod"])
            try:
                print("ztask_time_start: " + db_logs[i][j]["ztask_time_start"])
            except:
                print("************************************************************************oups y'a pas de ztask_time_start")

            try:
                print("ztask_line_start: " + str(db_logs[i][j]["ztask_line_start"]))
            except:
                print("************************************************************************oups y'a pas de ztask_line_start")

            try:
                print("ztask_time_end: " + db_logs[i][j]["ztask_time_end"])
            except:
                print("************************************************************************oups y'a pas de ztask_time_end")

            try:
                print("ztask_line_end: " + str(db_logs[i][j]["ztask_line_end"]))
            except:
                print("************************************************************************oups y'a pas de ztask_line_end")

            try:
                print("ztask_duration: " + str(db_logs[i][j]["ztask_duration"]))
            except:
                pass

            try:
                print("zwp_duration: " + str(db_logs[i][j]["zwp_duration"]))
            except:
                pass
        
            try:
                print("zratio_duration_wp_task: " + str(db_logs[i][j]["zratio_duration_wp_task"]))
            except:
                pass
        
        

def signal_handler(signal, frame):
    print("oups il y a eu un CTRL-C !")
    quit()
    # sys.exit(0)
  
def zget_unix_time(zdate):
    #    date_time_obj = datetime.datetime.strptime(zdate, '%Y-%m-%d %H:%M:%S.%f')
    zdate_time_obj = zdate
    if zverbose_unix_time: print("zdate_time_obj: [" + str(zdate_time_obj) + "]")
    zdate_time_1970_obj = datetime.datetime.strptime(
        "1970-01-01 02:00:00", '%Y-%m-%d %H:%M:%S')  # Astuce pour faire UTC-2 à cause de Grafana !
    if zverbose_unix_time: print("zdate_time_1970_obj: [" + str(zdate_time_1970_obj) + "]")
    zdate_time_unix_obj = (zdate_time_obj - zdate_time_1970_obj)
    if zverbose_unix_time: print("zdate_time_unix_obj: [" + str(zdate_time_unix_obj) + "]")
    return zdate_time_unix_obj


if (__name__ == "__main__"):
    print("\n" + version + "\n")

    signal.signal(signal.SIGINT, signal_handler)

    if len(sys.argv) == 1:
        print("Usage: ./parse-ansible-out4.py fichier_log_a_parser\n\n")
        sys.exit()

    zfile = open(sys.argv[1], "r")
    i = 1

    # on parse le fichier de logs
    while True:
        zline = zfile.readline()
        # est-ce la fin du fichier de logs ?
        if zline == "":
            break

        if zverbose_parsing: print("nouvelle ligne: " + str(i) + " " + zline[:-1])

        # est-ce une ligne de Task ?
        if zline.find(', TASK:') != -1:            
            if zverbose_parsing: print("coucou c'est une task")
            
            # récupération du task_site
            zstr_find1 = ' by zuzu, '
            p1 = zline.find(zstr_find1)
            zstr_find2 = ': PATH: '            
            p2 = zline.find(zstr_find2, p1)
            ztask_site_name = zline[p1 + len(zstr_find1):p2]
            if zverbose_parsing: print(str(i) + " ztask_site_name: [" + ztask_site_name + "]")

            # récupération du task_pod
            zstr_find1 = 'PATH: /'
            p1 = zline.find(zstr_find1)
            zstr_find2 = '_'            
            p2 = zline.find(zstr_find2, p1 + len(zstr_find1))
            ztask_pod = zline[p1 + len(zstr_find1):p2]
            if zverbose_parsing: print(str(i) + " ztask_pod: [" + ztask_pod + "]")

            # récupération du task_path
            zstr_find1 = '/ansible/'
            p1 = zline.find(zstr_find1)
            zstr_find2 = ', TASK: '            
            p2 = zline.find(zstr_find2, p1)
            ztask_path = zline[p1 + len(zstr_find1):p2]
            if zverbose_parsing: print(str(i) + " ztask_path: [" + ztask_path + "]")

            # récupération du task_name
            zstr_find1 = ' : '
            p1 = zline.find(zstr_find1)
            
            
            
            if zline.find(', action: ', p1) > 0:
                zstr_find2 = ', action: '            
                p2 = zline.find(zstr_find2, p1)
            else:
                zstr_find2 = ' at 2020'            
                p2 = zline.find(zstr_find2, p1)
            
            
            
            
            
            
            
            ztask_name = zline[p1 + len(zstr_find1):p2]
            if zverbose_parsing: print(str(i) + " ztask_name: [" + ztask_name + "]")
            
            # récupération du ztask_time start ou end
            zstr_find1 = ' at '
            p1 = zline.find(zstr_find1)
            # zstr_find2 = ''            
            # p2 = zline.find(zstr_find2, p1)
            if zline.find(', duration:', p1) > 0:
                zstr_find2 = ', duration:'            
                p2 = zline.find(zstr_find2, p1)
            else:
                p2 = -1
            ztask_time = zline[p1 + len(zstr_find1):p2]
            if zverbose_parsing: print(str(i) + " ztask_time: [" + ztask_time + "]")
            
            
            
            # est-ce un start ?
            if zline.find('log start') != -1:
                if zverbose_parsing: print("c'est un start")
                    
                # on cherche où se trouve la tâche dans le dictionnaire
                ztask_id = 0
                if zverbose_parsing: print("on cherche où se trouve la tâche dans le dictionnaire 114819")
                if zverbose_parsing: print("ztask_id_len 114441: " + str(len(db_logs)))
                for j in range(1, len(db_logs)+1):
                    if zverbose_parsing: print("j: " + str(j))
                    if db_logs[j]["ztask_path"] == ztask_path and db_logs[j]["ztask_name"] == ztask_name:
                        ztask_id = j
                        if zverbose_parsing: print("ztask_id 114543:" + str(ztask_id))
                        break

                if zverbose_parsing: print("ztask_id 102011: " + str(ztask_id))

                # avons-nous trouvé la tâche dans le dictionnaire ?
                if ztask_id == 0:
                    # La tâche n'existe pas encore, on la crée
                    if zverbose_parsing: print("la tâche n'existe pas encore, on la crée")
                    ztask_id = len(db_logs) + 1
                    if zverbose_parsing: print("ztask_id 1739: " + str(ztask_id))
                    db_logs[ztask_id] = {}
                    db_logs[ztask_id]["ztask_name"] = ztask_name
                    db_logs[ztask_id]["ztask_path"] = ztask_path

                # on cherche si le site n'existe pas déjà
                ztask_site_id = 0
                for j in range(1, (len(db_logs[ztask_id]) - 2) + 1):
                    if zverbose_parsing: print("j 190153: " + str(j))
                    if zverbose_parsing: print("ztask_site_name 1 190205: " + str(db_logs[ztask_id][j]["ztask_site_name"]))
                    if zverbose_parsing: print("ztask_site_name 2 190213: " + str(ztask_site_name))
                    if db_logs[ztask_id][j]["ztask_site_name"] == ztask_site_name:
                        ztask_site_id = j
                        if zverbose_parsing: print("ztask_site_id 190231:" + str(ztask_site_id))
                        break

                # est-ce que le site existe ?
                if ztask_site_id == 0:
                    if zverbose_parsing: print("le site n'existe pas, on doit le créer 190240: " + str(i))
                
                    # on calcul l'index du site dans le dictionnaire
                    ztask_site_id = (len(db_logs[ztask_id]) - 2) + 1
                    
                    if zverbose_parsing: print("ztask_id 180818: " + str(ztask_id))
                    if zverbose_parsing: print("ztask_site_id_len 111632: " + str((len(db_logs[ztask_id]) - 2)))
                    if zverbose_parsing: print("ztask_site_id 180818: " + str(ztask_site_id))
                    
                    # on crée le nouveau site et écrit le task_time_start
                    if zverbose_parsing: print("On crée un nouveau site et écrit le task_time_start")
                    if zverbose_parsing: print("ztask_site_name:" + str(ztask_site_name))
                    db_logs[ztask_id][ztask_site_id] = {}
                    db_logs[ztask_id][ztask_site_id]["ztask_site_name"] = ztask_site_name
                    db_logs[ztask_id][ztask_site_id]["ztask_pod"] = ztask_pod

                                
                # on écrit le task_time_start
                db_logs[ztask_id][ztask_site_id]["ztask_time_start"] = ztask_time
                db_logs[ztask_id][ztask_site_id]["ztask_line_start"] = i
                if zverbose_parsing: print("ztask_site_id_len 112027: " + str((len(db_logs[ztask_id]) - 2)))
                if zverbose_parsing: print("On a terminé de créer un nouveau site et d'écrire le task_time_start")


                
            # est-ce un end ?
            if zline.find('log end') != -1:                
                if zverbose_parsing: print("c'est un end")

                # on cherche où se trouve la tâche dans le dictionnaire
                ztask_id = 0
                if zverbose_parsing: print("on cherche où se trouve la tâche dans le dictionnaire 114844")                
                if zverbose_parsing: print("ztask_id_len 114225: " + str(len(db_logs)))
                for j in range(1, len(db_logs) + 1):
                    if zverbose_parsing: print("j 115336: " + str(j))
                    if db_logs[j]["ztask_path"] == ztask_path and db_logs[j]["ztask_name"] == ztask_name:
                        ztask_id = j
                        if zverbose_parsing: print("ztask_id 093236:" + str(ztask_id))
                        break         
                                   
                if zverbose_parsing: print("ztask_id 114634: " + str(ztask_id))
                    
                # avons-nous trouvé la tâche dans le dictionnaire ?
                if ztask_id == 0:
                    print("oups, y'a pas de tâche ici 133759")
                    print("et on doit s'arrêter !")
                    exit()
                
                # chercher l'index du site dans le dictionnaire
                ztask_site_id = 0
                for j in range(1, (len(db_logs[ztask_id]) - 2) + 1):
                    if zverbose_parsing: print("j 093501: " + str(j))
                    if zverbose_parsing: print("ztask_site_name 1 093547: " + str(db_logs[ztask_id][j]["ztask_site_name"]))
                    if zverbose_parsing: print("ztask_site_name 2 093547: " + str(ztask_site_name))
                    if db_logs[ztask_id][j]["ztask_site_name"] == ztask_site_name:
                        ztask_site_id = j
                        if zverbose_parsing: print("ztask_site_id 1133:" + str(ztask_site_id))
                        break

                # est-ce qu'il y a un site ?
                if ztask_site_id == 0:
                    if zverbose_parsing: print("oups, y'a pas de site ici 133935: " + str(i))
                    # break
                    # raw_input('Enter your input:')
                    # print("on s'arrête pour savoir pourquoi il n'y a pas de site ?")
                    # # print(db_logs)
                    # # zprint_db_log()
                    # print("boum on s'est arrêté ! 142745")
                    # exit()
                    
                    # on calcul l'index du site dans le dictionnaire
                    ztask_site_id = (len(db_logs[ztask_id]) - 2) + 1
                    if zverbose_parsing: print("ztask_site_id 1346:" + str(ztask_site_id))

                    # on crée un nouveau site
                    db_logs[ztask_id][ztask_site_id] = {}
                    db_logs[ztask_id][ztask_site_id]["ztask_site_name"] = ztask_site_name
                    db_logs[ztask_id][ztask_site_id]["ztask_pod"] = ztask_pod                
                
                # on écrit le task_time_end
                db_logs[ztask_id][ztask_site_id]["ztask_time_end"] = ztask_time
                db_logs[ztask_id][ztask_site_id]["ztask_line_end"] = i

                














            # est-ce une wp_duration ?
            if zline.find('log duration') != -1:                
                if zverbose_parsing: print("c'est une wp_duration")
                
                # récupération de la wp_duration
                zstr_find1 = ', duration: '
                p1 = zline.find(zstr_find1)
                p2 = -1
                zwp_duration = zline[p1 + len(zstr_find1):p2]
                if zverbose_parsing: print(str(i) + " zwp_duration: [" + zwp_duration + "]")
                
                
                # on cherche où se trouve la tâche dans le dictionnaire
                ztask_id = 0
                if zverbose_parsing: print("on cherche où se trouve la tâche dans le dictionnaire 114844")                
                if zverbose_parsing: print("ztask_id_len 114225: " + str(len(db_logs)))
                for j in range(1, len(db_logs) + 1):
                    if zverbose_parsing: print("j 115336: " + str(j))
                    # if db_logs[j]["ztask_path"] == ztask_path and db_logs[j]["ztask_name"] == ztask_name:
                    if db_logs[j]["ztask_name"] == ztask_name:
                        ztask_id = j
                        if zverbose_parsing: print("ztask_id 093236:" + str(ztask_id))
                        break         
                
                if zverbose_parsing: print("ztask_id 114634: " + str(ztask_id))
                
                # avons-nous trouvé la tâche dans le dictionnaire ?
                if ztask_id == 0:
                    print("oups, y'a pas de tâche ici 133759")
                    print("et on doit s'arrêter !")
                    exit()
                
                # chercher l'index du site dans le dictionnaire
                ztask_site_id = 0
                for j in range(1, (len(db_logs[ztask_id]) - 2) + 1):
                    if zverbose_parsing: print("j 093501: " + str(j))
                    if zverbose_parsing: print("ztask_site_name 1 093547: " + str(db_logs[ztask_id][j]["ztask_site_name"]))
                    if zverbose_parsing: print("ztask_site_name 2 093547: " + str(ztask_site_name))
                    if db_logs[ztask_id][j]["ztask_site_name"] == ztask_site_name:
                        ztask_site_id = j
                        if zverbose_parsing: print("ztask_site_id 1133:" + str(ztask_site_id))
                        break
                
                # est-ce qu'il y a un site ?
                if ztask_site_id == 0:
                    if zverbose_parsing: print("oups, y'a pas de site ici 133935: " + str(i))
                    # break
                    # raw_input('Enter your input:')
                    # print("on s'arrête pour savoir pourquoi il n'y a pas de site ?")
                    # # print(db_logs)
                    # # zprint_db_log()
                    # print("boum on s'est arrêté ! 142745")
                    # exit()
                
                    # on calcul l'index du site dans le dictionnaire
                    ztask_site_id = (len(db_logs[ztask_id]) - 2) + 1
                    if zverbose_parsing: print("ztask_site_id 1346:" + str(ztask_site_id))
                
                    # on crée un nouveau site
                    db_logs[ztask_id][ztask_site_id] = {}
                    db_logs[ztask_id][ztask_site_id]["ztask_site_name"] = ztask_site_name
                    db_logs[ztask_id][ztask_site_id]["ztask_pod"] = ztask_pod                
                
                # # on écrit le task_time_end
                # db_logs[ztask_id][ztask_site_id]["ztask_time_end"] = ztask_time
                # db_logs[ztask_id][ztask_site_id]["ztask_line_end"] = i
                
                # on écrit la wp_duration
                db_logs[ztask_id][ztask_site_id]["zwp_duration"] = zwp_duration
            


















            
            

        if zverbose_parsing: print("next: " + str(i))
        i = i + 1
        # on évite la boucle infinie ;-)
        if i > zloop_parse:
            break

    zfile.close()

    if zverbose_parsing: print("\n\non a terminé de parser les logs 161447\n\n")
    
        
    # on calcul les durations pour chaque sites
    for i in range(1, len(db_logs)+1): 
        if zverbose_duration: print("i: " + str(i))
        for j in range(1, (len(db_logs[i]) - 2) + 1):
            if zverbose_duration: print("ztask_site_name: " + str(j) + ", " + db_logs[i][j]["ztask_site_name"])
            try:
                ztask_time_1 = db_logs[i][j]["ztask_time_start"][0:-6]
                if zverbose_duration: print("ztask_time_1: " + str(ztask_time_1))
                ztask_time_obj_1 = datetime.datetime.strptime(ztask_time_1, '%Y-%m-%d %H:%M:%S.%f')
                ztask_unix_time_1 = zget_unix_time(ztask_time_obj_1).total_seconds()
                if zverbose_duration: print("ztask_unix_time_1: " + str(ztask_unix_time_1))
                try:
                    ztask_time_2 = db_logs[i][j]["ztask_time_end"][0:-6]
                    if zverbose_duration: print("ztask_time_2: " + str(ztask_time_2))
                    ztask_time_obj_2 = datetime.datetime.strptime(ztask_time_2, '%Y-%m-%d %H:%M:%S.%f')
                    ztask_unix_time_2 = zget_unix_time(ztask_time_obj_2).total_seconds()
                    if zverbose_duration: print("ztask_unix_time_2: " + str(ztask_unix_time_2))
                    ztask_duration = ztask_unix_time_2 - ztask_unix_time_1
                    if zverbose_duration: print("ztask_duration: " + str(ztask_duration))
                    db_logs[i][j]["ztask_duration"] = ztask_duration
                    
                    
                    try:
                        zwp_duration = db_logs[i][j]["zwp_duration"]
                        if zverbose_duration: print("zwp_duration: " + str(zwp_duration))
                        zratio_duration_wp_task = float(zwp_duration) / float(ztask_duration)
                        if zverbose_duration: print("zratio_duration_wp_task: " + str(zratio_duration_wp_task))
                        db_logs[i][j]["zratio_duration_wp_task"] = zratio_duration_wp_task
                    except:
                        if zverbose_duration: print("oups, il n'y a pas de zwp_duration ici 160124")
                    
                    
                    
                    
                    
                    if zverbose_duration: print(".................................................. 110232")                        
                    if zverbose_duration: print("Task number: " + str(i))
                    if zverbose_duration: print("ztask_name: " + str(i) + ", " + db_logs[i]["ztask_name"])
                    if zverbose_duration: print("ztask_path: " + db_logs[i]["ztask_path"])
                    if zverbose_duration: print("ztask_site_name: " + str(j) + ", " + db_logs[i][j]["ztask_site_name"])
                    if zverbose_duration: print("ztask_time_start: " + db_logs[i][j]["ztask_time_start"])
                    if zverbose_duration: print("ztask_line_start: " + str(db_logs[i][j]["ztask_line_start"]))
                    if zverbose_duration: print("ztask_time_end: " + db_logs[i][j]["ztask_time_end"])
                    if zverbose_duration: print("ztask_line_end: " + str(db_logs[i][j]["ztask_line_end"]))
                    if zverbose_duration: print("ztask_duration: " + str(db_logs[i][j]["ztask_duration"]))


                    try:
                        if zverbose_duration: print("zwp_duration: " + str(db_logs[i][j]["zwp_duration"]))
                        if zverbose_duration: print("zratio_duration_wp_task: " + str(db_logs[i][j]["zratio_duration_wp_task"]))
                    except:
                        if zverbose_duration: print("oups, y'a pas de ratio ici 160535")


                    if zverbose_duration: print("..................................................")                    
                except:
                    if zverbose_duration: print("oups, c'est pas bon ici 121330")
            except:
                if zverbose_duration: print("oups, c'est pas bon ici 121313")


    if zverbose_duration: print("\n\non a terminé de calculer les durations 141249\n\n")

    if zverbose_dico: zprint_db_log()

            
            
    # on envoie les données à la db influxdb/grafana    
    if zmake_curl:
        for i in range(1, len(db_logs)+1): 
            if zverbose_curl: print("ztask_path_id 121552: " + str(i) + db_logs[i]["ztask_path"])
            for j in range(1, (len(db_logs[i]) - 2) + 1):
                if zverbose_curl: print("ztask_site_name: " + str(j) + ", " + db_logs[i][j]["ztask_site_name"])

                try:
                    ztask_name_1 = db_logs[i]["ztask_name"]
                    ztask_path_1 = db_logs[i]["ztask_path"]
                    ztask_line_1 = db_logs[i][j]["ztask_line_start"]
                    ztask_site_name_1 = db_logs[i][j]["ztask_site_name"]
                                    
                    # on change tous les caractères *system* utilisés par InfluxDB
                    ztask_name = ztask_name_1.replace("“", "")
                    ztask_name = ztask_name_1.replace("”", "")
                    ztask_name = ztask_name_1.replace('"', "")
                    ztask_name = ztask_name_1.replace(" ", "_")
                    ztask_path = ztask_path_1.replace(" ", "_")
                    ztask_path = ztask_path.replace(":", "_")
                    ztask_path = ztask_path.replace(".", "_")
                    ztask_site_name = ztask_site_name_1
                    
                    # on transforme en nano secondes pour InfluxDB
                    ztask_time_1 = db_logs[i][j]["ztask_time_start"][0:-6]
                    if zverbose_curl: print("ztask_time_1: " + ztask_time_1)

                    ztask_time_obj_1 = datetime.datetime.strptime(ztask_time_1, '%Y-%m-%d %H:%M:%S.%f')
                    ztask_unix_time_1 = zget_unix_time(ztask_time_obj_1).total_seconds()
                    ztask_unix_time_nano = ztask_unix_time_1 * 1000000000

                    try:
                        ztask_duration = db_logs[i][j]["ztask_duration"]
                        zcmd = 'curl -i -XPOST "$dbflux_srv_host:$dbflux_srv_port/write?db=$dbflux_db&u=$dbflux_u_user&p=$dbflux_p_user"  --data-binary "' + zinfluxdb_table
                        zcmd = zcmd + ',task=' + ztask_name + '_/_' + ztask_path + ',site=' + ztask_site_name + ' duration=' + str(ztask_duration) + ' ' + '%0.0f' % (ztask_unix_time_nano) + '"'
                        
                        if zverbose_curl: print(zcmd)
                        
                        if zsend_grafana:
                            zerr = os.system(zcmd)
                            if zerr != 0:
                                if zverbose_grafana(): print(zerr)
                    except:
                        print("oups, y'a pas de duration ici 144852")
                except:
                    print("oups, y'a pas de start ici 154446")
            # on évite la boucle infinie ;-)
            if zverbose_curl: print("toto:" + str(i))
            if i > zloop_curl:
                break
                
                
                
    # on calcul le résumé du profiling    
    if zmake_profiling:
        print(sys.argv[1]) + " start at " + db_logs[1][1]["ztask_time_start"][0:-6]
        print("".ljust(100, '*'))
        ztask_duration_total = 0
        
        zratio_duration_wp_task_total_sum = 0
        zratio_duration_wp_task_total_number = 0
        zratio_duration_wp_task_total_mid = 0
        
        zduration_wp_total_sum = 0
        zduration_task_total_sum = 0
        
        
        for i in range(1, len(db_logs)+1):
            if zverbose_profiling: print("i 115711: " + str(i))
            # if i == 9:
                # print(db_logs[i])
                # zprint_db_log()
                # # print("toto")
                # # import numpy as np
                # # print(np.matrix(db_logs[i]))
                # # print("tutu")
                # # print(db_logs[i].__str__())
            ztask_time_start = db_logs[i][1]["ztask_time_start"][0:-6]
            ztask_time_end = db_logs[i][len(db_logs[i]) - 2]["ztask_time_end"][0:-6]
            if zverbose_profiling: print("ztask_time_start: " + ztask_time_start)
            if zverbose_profiling: print("ztask_time_end: " + ztask_time_end)
            
            ztask_time_1 = db_logs[i][1]["ztask_time_start"][0:-6]
            if zverbose_profiling: print("ztask_time_1: " + str(ztask_time_1))
            ztask_time_obj_1 = datetime.datetime.strptime(ztask_time_1, '%Y-%m-%d %H:%M:%S.%f')
            ztask_unix_time_1 = zget_unix_time(ztask_time_obj_1).total_seconds()
            if zverbose_profiling: print("ztask_unix_time_1: " + str(ztask_unix_time_1))

            ztask_time_2 = db_logs[i][len(db_logs[i]) - 2]["ztask_time_end"][0:-6]
            if zverbose_profiling: print("ztask_time_2: " + str(ztask_time_2))
            ztask_time_obj_2 = datetime.datetime.strptime(ztask_time_2, '%Y-%m-%d %H:%M:%S.%f')
            ztask_unix_time_2 = zget_unix_time(ztask_time_obj_2).total_seconds()
            if zverbose_profiling: print("ztask_unix_time_2: " + str(ztask_unix_time_2))

            ztask_duration = ztask_unix_time_2 - ztask_unix_time_1
            if zverbose_profiling: print("ztask_duration: " + str(ztask_duration))


            if zverbose_profiling: print("Calcul des stats du ratio...")


            zratio_duration_wp_task_min = 1.1
            zratio_duration_wp_task_max = 0
            zratio_duration_wp_task_sum = 0
            zratio_duration_wp_task_number = 0
            zratio_duration_wp_task_mid = 0
            zduration_wp_sum = 0
            zduration_task_sum = 0
            
            for j in range(1, (len(db_logs[i]) - 2) + 1):
                if zverbose_profiling: print("ztask_site_name: " + str(j) + ", " + db_logs[i][j]["ztask_site_name"])
            
                try:
                    zratio_duration_wp_task = float(db_logs[i][j]["zratio_duration_wp_task"])
                    if zverbose_profiling: print("zratio_duration_wp_task: " + str(zratio_duration_wp_task))
                    if zratio_duration_wp_task < zratio_duration_wp_task_min: zratio_duration_wp_task_min = zratio_duration_wp_task
                    if zratio_duration_wp_task > zratio_duration_wp_task_max: zratio_duration_wp_task_max = zratio_duration_wp_task
                    zratio_duration_wp_task_sum = zratio_duration_wp_task_sum + zratio_duration_wp_task
                    zratio_duration_wp_task_number = zratio_duration_wp_task_number + 1
                    
                    zduration_wp_sum = zduration_wp_sum + float(db_logs[i][j]["zwp_duration"])
                    zduration_task_sum = zduration_task_sum + float(db_logs[i][j]["ztask_duration"])
                    
                    
                except:
                    pass

            if zratio_duration_wp_task_number > 0:
                zratio_duration_wp_task_mid = zratio_duration_wp_task_sum / zratio_duration_wp_task_number
                zratio_duration_wp_task_total_sum = zratio_duration_wp_task_total_sum + zratio_duration_wp_task_mid
                zratio_duration_wp_task_total_number = zratio_duration_wp_task_total_number + 1
            
            if zratio_duration_wp_task_min > 1: zratio_duration_wp_task_min = 0
            if zverbose_profiling: print("zratio_duration_wp_task_min: " + str(zratio_duration_wp_task_min))
            if zverbose_profiling: print("zratio_duration_wp_task_max: " + str(zratio_duration_wp_task_max))
            if zverbose_profiling: print("zratio_duration_wp_task_mid: " + str(zratio_duration_wp_task_mid))

            try:
                zduration_wp_total_sum = zduration_wp_total_sum + zduration_wp_sum
                zduration_task_total_sum = zduration_task_total_sum + zduration_task_sum
            except:
                pass


            zstring = str(i) + " ../" + db_logs[i]["ztask_path"] + ", " + db_logs[i]["ztask_name"]
            # enlève les guillemets typographiques à la con
            zstring = zstring.replace("“", '"')
            zstring = zstring.replace("”", '"')
            zstring = zstring[0:95] + " "
            zstring2 = zstring.ljust(100, '-')
            zstring2 = zstring2 + str('{:.2f}'.format(ztask_duration)).rjust(9, " ")

            zstring2 = zstring2 + ", task sum: " + str('{:.2f}'.format(zduration_task_sum))
            zstring2 = zstring2 + ", wp sum: " + str('{:.2f}'.format(zduration_wp_sum))
            
            # zstring2 = zstring2 + ", wp/task min: " + str('{:.2f}'.format(zratio_duration_wp_task_min))
            # zstring2 = zstring2 + ", wp/task max: " + str('{:.2f}'.format(zratio_duration_wp_task_max))
            zstring2 = zstring2 + ", wp/task mid: " + str('{:.2f}'.format(zratio_duration_wp_task_mid))
            
            # print(zstring.ljust(100, '-') + str('{:.2f}'.format(ztask_duration)).rjust(9, " ")) + ", wp/task: " + str('{:.2f}'.format(zratio_duration_wp_task_mid))
            print(zstring2)
            ztask_duration_total = ztask_duration_total + ztask_duration

            # on évite la boucle infinie ;-)
            # if zverbose_profiling: print("toto:" + str(i))
            if i > zloop_profiling:
                break
        # print("Total".ljust(100, '*') + str('{:.2f}'.format(ztask_duration_total)).rjust(9, " ") + "\n")
    print("".ljust(100, '*'))
        
    ztask_time_1 = db_logs[1][1]["ztask_time_start"][0:-6]
    if zverbose_profiling: print("ztask_time_1: " + str(ztask_time_1))
    ztask_time_obj_1 = datetime.datetime.strptime(ztask_time_1, '%Y-%m-%d %H:%M:%S.%f')
    ztask_unix_time_1 = zget_unix_time(ztask_time_obj_1).total_seconds()
    if zverbose_profiling: print("ztask_unix_time_1: " + str(ztask_unix_time_1))

    i = len(db_logs)
    ztask_time_2 = db_logs[i][len(db_logs[i]) - 2]["ztask_time_end"][0:-6]
    if zverbose_profiling: print("ztask_time_2: " + str(ztask_time_2))
    ztask_time_obj_2 = datetime.datetime.strptime(ztask_time_2, '%Y-%m-%d %H:%M:%S.%f')
    ztask_unix_time_2 = zget_unix_time(ztask_time_obj_2).total_seconds()
    if zverbose_profiling: print("ztask_unix_time_2: " + str(ztask_unix_time_2))
    
    ztask_duration_total = ztask_unix_time_2 - ztask_unix_time_1

    zratio_duration_wp_task_total_mid = zratio_duration_wp_task_total_sum / zratio_duration_wp_task_total_number

    print("Playbook run took: " + str(datetime.timedelta(seconds=round(ztask_duration_total))) + ", wp/task : " + str('{:.2f}'.format(zratio_duration_wp_task_total_mid)) + "\n")
    print("zduration_task_total_sum: " + str('{:.2f}'.format(zduration_task_total_sum)))
    print("zduration_wp_total_sum: " + str('{:.2f}'.format(zduration_wp_total_sum)))
    print("zratio_total_sum: " + str('{:.2f}'.format(zduration_wp_total_sum / zduration_task_total_sum)))
    
    
    