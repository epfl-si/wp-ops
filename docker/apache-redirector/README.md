# Apache Redirector

A minimal [httpd] container to manage redirections.

The redirection 3xx are defined in [rfc9110]:
> The 3xx (Redirection) class of status code indicates that further action needs
> to be taken by the user agent in order to fulfill the request. There are
> several types of redirects:
> 1. Redirects that indicate this resource might be available at a different
>    URI, as provided by the Location header field, as in the status codes [301
>    (Moved Permanently)], [302 (Found)], [307 (Temporary Redirect)], and [308
>    (Permanent Redirect)].
> 2. Redirection that offers a choice among matching resources capable of
>    representing this resource, as in the 300 (Multiple Choices) status code.
> 3. Redirection to a different resource, identified by the Location header
>    field, that can represent an indirect response to the request, as in the
>    303 (See Other) status code.
> 4. Redirection to a previously stored result, as in the 304 (Not Modified)
>    status code.

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
[rfc9110]: https://www.rfc-editor.org/rfc/rfc9110.html#name-redirection-3xx
[301 (Moved Permanently)]: https://www.rfc-editor.org/rfc/rfc9110.html#status.301
[302 (Found)]: https://www.rfc-editor.org/rfc/rfc9110.html#status.302
[307 (Temporary Redirect)]: https://www.rfc-editor.org/rfc/rfc9110.html#status.307
[308 (Permanent Redirect)]: https://www.rfc-editor.org/rfc/rfc9110.html#status.308
