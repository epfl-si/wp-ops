# Menu API

An express server that can serves WordPress menu.


## Development

* `docker build -t epflsi/menu-api .`
* `docker run --name menu-api -it -p 8888:3000 epflsi/menu-api`
* `docker rm -f menu-api && docker build -t epflsi/menu-api . && docker run -d --name menu-api -it -p 8888:3000 epflsi/menu-api`
* Then use `docker logs -f menu-api`


### Test

```
curl http://localhost:8888/breadcrumb?lang=fr&url=https://www.epfl.ch/campus/services/website/
```
or
```
php test.php
```
