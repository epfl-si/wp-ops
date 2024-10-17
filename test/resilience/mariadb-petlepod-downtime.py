import concurrent.futures
import importlib
import json
import os
import subprocess
import sys
import time
import venv

# ----------------------------------------------------------- ensure python venv
# REQUIRED_PACKAGES = ['kubernetes', 'requests', 'urllib3']
# VENV_DIR = 'wpresi'

# if os.environ.get('VIRTUAL_ENV') is None:
#   if not os.path.exists(VENV_DIR):
#     # courtesy of chatGPT ;)
#     venv.EnvBuilder(with_pip=True).create(VENV_DIR)

#   activate_script = os.path.join(VENV_DIR, 'bin', 'activate')

#   # with open(activate_script) as f:
#   #     exec(f.read(), {'__file__': activate_script})
#   os.system("source " + activate_script)

#   # restart script
#   print("Self restarting", file=sys.stderr)
#   os.execv(sys.executable, ['python3'] + sys.argv)
  
# missing_packages = []
# for package in REQUIRED_PACKAGES:
#   try:
#     importlib.import_module(package)
#   except ImportError:
#     missing_packages.append(package)

# if missing_packages:
#   subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)

# ------------------------------------------------------------ the actual script

from kubernetes import client as kclient, config as kconfig
import requests
import urllib3

kconfig.load_kube_config()
urllib3.disable_warnings()

# k8s=kclient.CoreV1Api()
# pod=k8s.read_namespaced_pod('mariadb-min-0', 'wordpress-test')
# print(pod.status.phase)
# print("---- kill")
# res = k8s.delete_namespaced_pod('mariadb-min-0', 'wordpress-test', propagation_policy='Foreground')
# while True:
#   pod=k8s.read_namespaced_pod('mariadb-min-0', 'wordpress-test')
#   print(pod.status.phase)
#   time.sleep(0.1)
# exit()

BASEURL="https://wpn.fsd.team"
URLS = list(map(lambda p: BASEURL+p, [    # ruby I whish you were here !
    "/labs/mechanical-spectroscopy/",
    "/schools/sb/sph/",
    "/research/facilities/cmi/",
    "/labs/lcav/",
    "/education/phd/edpy-physics/",
    "/education/bachelor/",
    "/campus/associations/list/irrotationnels/",
]))

class PodPetter:
  def __init__(self, namespace='wordpress-test', urls=[], wait_sleep=0.5):
    self.ns = namespace
    self.urls = urls if urls else URLS
    self.k8s = kclient.CoreV1Api()
    self.ws = wait_sleep

  def wait_url(self, url, up=True):
    dt0 = time.time()
    while True:
      # timer starts imediatelly but it is useless to check imediatelly
      # therefore sleep is at the beginning of the loop
      time.sleep(self.ws)
      try:
        rt0 = time.time()
        response = requests.get(url, timeout=5, verify=False)
        rt1 = time.time()
        if up and response.status_code == 200 or not up and response.status_code != 200:
          dt1 = time.time()
          ret = {
            "url":       url,
            "code":      response.status_code,
            "resp_time": rt1-rt0,
            "wait_time": dt1-dt0,
          }
          return ret
      except requests.RequestException as e:
        # print(f"Error with {url}: {e}. Retrying...", file=sys.stderr)
        pass
 
  def wait_urls(self, up=True):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
      futures = [executor.submit(self.wait_url, url, up) for url in self.urls]

      for future in concurrent.futures.as_completed(futures):
        result = future.result()
        results.append(result);
    return results

  def pod_running(self, pod='mariadb-min-0'):
    res=self.k8s.read_namespaced_pod(pod, self.ns)
    return res.status.phase == "Running"

  def petlepod(self, pod='mariadb-min-0'):
    if not self.pod_running(pod):
      return True
    try:
      # ret = self.k8s.delete_namespaced_pod(name=pod, namespace=self.ns, dry_run='All', grace_period_seconds=0, propagation_policy='Foreground')
      ret = self.k8s.delete_namespaced_pod(name=pod, namespace=self.ns)
      while self.pod_running(pod):
        time.sleep(0.1)
      return True
    except kclient.rest.ApiException as e:
      # print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e, file=sys.stderr)
      return False

  def run(self, nrep=1):
    allresults = []
    for irep in range(nrep):
      while not self.petlepod():
        time.sleep(1)

      # TODO: check that pod is down and that sites are not working
      time.sleep(2)
      results = self.wait_urls()
      for e in results:
        e['irep'] = irep
        print(json.dumps(e)+",", file=sys.stderr)
      allresults.extend(results)
    return allresults

pp = PodPetter()
results = pp.run(500)
results_json = json.dumps(results)
print(results_json)
