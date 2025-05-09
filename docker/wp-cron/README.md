```
pip install -r requirements.txt
pip install -r requirements_dev.txt

python3 test/mock_pushgateway.py

export K8S_NAMESPACE=svc0041t-wordpress
export DEBUG=1
python3 wp-cron.py --pushgateway=localhost:8083
```
