DATABASES = {
    'default': {
        'ATOMIC_REQUESTS': True,
        'ENGINE': 'awx.main.db.profiled_pg',
        'NAME': "{{ awx_postgresql_database['name'] }}",
        'USER': "{{ awx_postgresql_database['user'] }}",
        'PASSWORD': "{{ awx_postgresql_database['password'] | eyaml(eyaml_keys) | trim_lines | b64encode }}",
        'HOST': "{{ awx_postgresql_database['host'] }}",
        'PORT': "{{ awx_postgresql_database['port'] }}",
    }
}
BROKER_URL = 'amqp://{}:{}@{}:{}/{}'.format(
    "awx",
    "{{ awx_postgresql_database['password'] | eyaml(eyaml_keys) | trim_lines | b64encode }}",
    "localhost",
    "5672",
    "awx")
CHANNEL_LAYERS = {
    'default': {'BACKEND': 'asgi_amqp.AMQPChannelLayer',
                'ROUTING': 'awx.main.routing.channel_routing',
                'CONFIG': {'url': BROKER_URL}}
}
