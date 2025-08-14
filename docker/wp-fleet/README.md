```
pip install -r requirements.txt
```
`oc port-forward service/mariadb-fleet 3306:3306`

Retrieve password for mariadb:
`oc extract secret/wp-fleet --to=-`

Login into OS4 and then:
```
export K8S_NAMESPACE=svc0041t-wordpress
export MARIADB_PASSWORD="XXX" # Put here the password retreived
export MARIADB_HOST=127.0.0.1
python3 wp-fleet.py
```
