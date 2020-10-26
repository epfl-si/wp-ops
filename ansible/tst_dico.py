#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Petit script pour tester la création de dictionnaires en Python

version = "tst_dico.py  zf200901.1837 "

db_logs = {}
ztask_number = 0        # le zéro est important car on l'utilise pour savoir si on est au début du dictionnaire !
ztask_id = 0
ztask_line = 0
ztask_name = ""
ztask_path = ""
ztask_site = ""
ztask_time = ""
ztask_duration = 0


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



if (__name__ == "__main__"):
    print("\n" + version + "\n")


    
    ztask_name1 = "toto"
    ztask_path1 = "tutu"
    ztask_name2 = "titi"
    ztask_path2 = "tata"
    
    ztask_site1 = "site1"
    ztask_time1 = "1234"
    ztask_site2 = "site2"
    ztask_time2 = "2345"
    ztask_site3 = "site3"
    ztask_time3 = "3456"

    ztask_number = 1
    ztask_site_number = 1

    db_logs[ztask_number] = {}
    db_logs[ztask_number]["ztask_name"] = ztask_name1
    db_logs[ztask_number]["ztask_path"] = ztask_path1
    print(len(db_logs[ztask_number]))
    
    db_logs[ztask_number][ztask_site_number] = {}
    db_logs[ztask_number][ztask_site_number]["ztask_site_name"] = ztask_site1
    db_logs[ztask_number][ztask_site_number]["ztask_time"] = ztask_time1
    print(len(db_logs[ztask_number]))
    
    ztask_site_number = ztask_site_number + 1

    db_logs[ztask_number][ztask_site_number] = {}
    db_logs[ztask_number][ztask_site_number]["ztask_site_name"] = ztask_site2
    db_logs[ztask_number][ztask_site_number]["ztask_time"] = ztask_time2

    ztask_site_number = ztask_site_number + 1

    db_logs[ztask_number][ztask_site_number] = {}
    db_logs[ztask_number][ztask_site_number]["ztask_site_name"] = ztask_site3
    db_logs[ztask_number][ztask_site_number]["ztask_time"] = ztask_time3

    ztask_number = ztask_number + 1
    ztask_site_number = 1

    db_logs[ztask_number] = {}
    db_logs[ztask_number]["ztask_name"] = ztask_name1
    db_logs[ztask_number]["ztask_path"] = ztask_path1
    
    db_logs[ztask_number][ztask_site_number] = {}
    db_logs[ztask_number][ztask_site_number]["ztask_site_name"] = ztask_site1
    db_logs[ztask_number][ztask_site_number]["ztask_time"] = ztask_time1

    ztask_site_number = ztask_site_number + 1
    db_logs[ztask_number][ztask_site_number] = {}
    db_logs[ztask_number][ztask_site_number]["ztask_site_name"] = ztask_site2
    db_logs[ztask_number][ztask_site_number]["ztask_time"] = ztask_time2


    print(db_logs)
    print(len(db_logs))
    print(len(db_logs[1]))
    print(len(db_logs[2]))
    
    ztask_number = 1
    ztask_site_number = 2
    print("")
    print(db_logs[ztask_number]["ztask_name"])
    print(db_logs[ztask_number]["ztask_path"])
    print(db_logs[ztask_number][ztask_site_number]["ztask_site_name"])
    print(db_logs[ztask_number][ztask_site_number]["ztask_time"])

