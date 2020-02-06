#!/usr/bin/python3

import json


def compare_two(d1, d2, parents=""):

    path_str = 'Path: {}'.format(parents)
    if isinstance(d1, dict):
    
        # Comparing keys
        for k in d1:
            if k not in d2:
                print('Missing key {} in dict d2 - {}'.format(k, path_str))
            else:
                compare_two(d1[k], d2[k], '{} > {}'.format(parents, k))

    elif isinstance(d1, list):
        
        if set(d1) != set(d2):
            print('Different list: {} vs {} - {}'.format(d1, d2, path_str))

    else:
        if d1 != d2:
            print('Different values: {} vs {} - {}'.format(d1, d2, path_str))









env='test'

with open('/tmp/inventory.perl.{}'.format(env)) as json_file:
    pe = json.load(json_file)

with open('/tmp/inventory.python.{}'.format(env)) as json_file:
    py = json.load(json_file)



compare_two(pe, py)
