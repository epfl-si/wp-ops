```
pip install -r requirements.txt
pip install -r requirements_dev.txt

python3 test/mock_pushgateway.py
```
Login into OKD and then:
```
export K8S_NAMESPACE=wordpress-test
export DEBUG=1
python3 wp-cron.py --pushgateway=localhost:8083
```

## To build wp-cron manually
Change version in wp-ops/ansible/roles/wordpress-namespace/tasks/wp-cron.yml
`make -C ~/dev/wp-dev-nginx wp-base wp-cron wp-cron-push && wpsible -t wp.cron [--prod]`

## To build on OS4
`wpsible -t wp.cron.rebuild`
`wpsible -t wp.cron [--prod]`
