import subprocess

class WordpressSite:
    def __init__(self, ingress, wp):
        self._ingress = ingress
        self._wp = wp
    
    def run_cron(self):
        try:
            subprocess.run(['wp', f'--ingress={self._ingress_name()}', 'cron', 'event', 'run', '--due-now'], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running wp cron: {e}")
            return False

    def _ingress_name(self):
        return self._ingress['metadata']['name']
