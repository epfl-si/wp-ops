import yaml
import os

def kube_credentials(name_suffix):
    kubeconfig_path = os.path.join(os.getenv("HOME"), ".kube", "config")
    kubeconfig = yaml.safe_load(open(kubeconfig_path))
    #XXX
    # comments
    cred = list(filter(lambda x: "pub-os-exopge-epfl-ch" in x['name'], kubeconfig['users']))
    return {
        "user": cred[0]['name'].split('/')[0],
        "token": cred[0]['user']['token']
    }

def contains_c2c_secret_link(raw_yaml, secret_name):
    
    
    imagePullSecretName = list(filter(lambda x: secret_name in x['name'], raw_yaml['imagePullSecrets']))
    return len(imagePullSecretName) > 0
	

class FilterModule(object):
    def filters(self):
        return {
            'contains_c2c_secret_link':  contains_c2c_secret_link,
            'kube_credentials':  kube_credentials
        }