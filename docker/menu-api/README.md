# Menu API

An express server that can serves WordPress menu.


## Development

* `docker build -t epflsi/menu-api .`
* `docker run --name menu-api -it -p 8888:3000 epflsi/menu-api`
* `docker rm -f menu-api && docker build -t epflsi/menu-api . && docker run -d --name menu-api -it -p 8888:3000 epflsi/menu-api`
* Then use `docker logs -f menu-api`


### Test

```
curl http://localhost:8888/breadcrumb\?blogname\=https://go.epfl.ch/tutu\&lang\=en
```
or
```
php test.php
```
