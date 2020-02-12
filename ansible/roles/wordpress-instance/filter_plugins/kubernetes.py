import yaml
import os
import re

def uri_filter(raw_yaml):
    
    #XXX
    # comments
    
    return raw_yaml["spec"]["host"]

def latest_bkp(raw_bash):

    bkps = list(filter(lambda x: "full" in x, raw_bash.split("\n")))
    dates = list(map( lambda x: x.split("_")[0], bkps ))
    bkp_archive_name= max(dates)+"_full.tar.gz"
    bkp_sql_name= max(dates)+"_full.sql"
    return bkp_archive_name

def sanitize_tar_path(path):
    path = re.sub(r'/+','/', path)
    path = re.sub(r'^/', '', path)
    return path


class FilterModule(object):
    def filters(self):
        return {
            'uri_filter':  uri_filter,
            'latest_bkp': latest_bkp,
            'sanitize_tar_path':sanitize_tar_path
        }
