# Maximum ?page_size= value in API queries
MAX_PAGE_SIZE = 1000

AWX_PROOT_ENABLED = False
AWX_AUTO_DEPROVISION_INSTANCES = True

AWX_CONTAINER_GROUP_DEFAULT_NAMESPACE = "{{ ansible_oc_namespace }}"

CLUSTER_HOST_ID = socket.gethostname()
SYSTEM_UUID = '00000000-0000-0000-0000-000000000000'

REMOTE_HOST_HEADERS = ['HTTP_X_FORWARDED_FOR']
ALLOWED_HOSTS = ['*']
INTERNAL_API_URL = 'http://127.0.0.1:8052'

# Appears to be required for proper `receptor` interoperation:
IS_K8S = True

SECRET_KEY = open('/etc/tower/conf.d/django_secret_key', 'rb').read().strip()

# Use mirrored images for awx-ee ephemeral pods:
GLOBAL_JOB_EXECUTION_ENVIRONMENTS = [{'name': 'AWX EE ({{ awx_ee_version }})', 'image': '{{ awx_ee_image_for_pods }}'}]
CONTROL_PLANE_EXECUTION_ENVIRONMENT = '{{ awx_ee_image_for_pods }}'


{% if awx_verbose | default(False) %}
RECEPTOR_RELEASE_WORK = False

LOG_AGGREGATOR_LEVEL = 'DEBUG'
LOGGING['handlers']['console']['()'] = 'awx.main.utils.handlers.ColorHandler'
LOGGING['handlers']['task_system'] = LOGGING['handlers']['console'].copy()

{% endif %}
