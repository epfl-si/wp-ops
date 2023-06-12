# Maximum ?page_size= value in API queries
MAX_PAGE_SIZE = 1000

AWX_PROOT_ENABLED = False
AWX_AUTO_DEPROVISION_INSTANCES = True

CLUSTER_HOST_ID = socket.gethostname()
SYSTEM_UUID = '00000000-0000-0000-0000-000000000000'

REMOTE_HOST_HEADERS = ['HTTP_X_FORWARDED_FOR']
ALLOWED_HOSTS = ['*']
INTERNAL_API_URL = 'http://127.0.0.1:8052'

# Appears to be required for proper `receptor` interoperation:
IS_K8S = True

SECRET_KEY = open('/etc/tower/conf.d/django_secret_key', 'rb').read().strip()

{% if awx_verbose | default(False) %}
RECEPTOR_RELEASE_WORK = False

LOG_AGGREGATOR_LEVEL = 'DEBUG'
LOGGING['handlers']['console']['()'] = 'awx.main.utils.handlers.ColorHandler'
LOGGING['handlers']['task_system'] = LOGGING['handlers']['console'].copy()

{% endif %}
