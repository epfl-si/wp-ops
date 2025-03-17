# Apache Redirector

A minimal [httpd] container to manage redirections.

## Local

First, configure your `/etc/hosts`:
```
127.0.0.1 labs.epfl.ch
127.0.0.1 redirect.epfl.ch
127.0.0.1 rewrite.epfl.ch
```

Then, set up the container
1. `docker build -t apache-redirector .`
2. ```sh
   docker run -dit -p 8080:8080 \
     -v ./test/subdomains:/srv/subdomains \
     --rm --name apache-redirector \
     apache-redirector httpd-foreground
   ``` 
3. `docker logs -f apache-redirector`

## Remote (kubernetes)

Edit your `/etc/hosts` file to match the ClusterIP.

Change the [routes.yml](./test/routes.yml) file to match your hostname and 
namespace. Create the Kubernetes's objects and run the tests below.

## Tests

You can test these URLs

- A file with 2 RewriteRules:
  - `curl -I http://labs.epfl.ch:8080`
    ```sh
    HTTP/1.1 301 Moved Permanently
    Location: https://www.epfl.ch/labs/
    ```
  - `curl -I http://labs.epfl.ch:8080/decode`
    ```sh
    HTTP/1.1 301 Moved Permanently
    Location: https://www.epfl.ch/labs/decode/
    ```
- A file with a Redirect:  
  `curl -I http://redirect.epfl.ch:8080`
  ```sh
  HTTP/1.1 302 Found
  Location: https://zombo.com
  ```
- A file with a RewriteRules:  
  `curl -I http://rewrite.epfl.ch:8080/this/is/zombocom`
  ```sh
  HTTP/1.1 303 See Other
  Location: https://zombo.com/this/is/zombocom
  ```


[httpd]: https://hub.docker.com/_/httpd
