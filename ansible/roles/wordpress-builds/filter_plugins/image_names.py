import re

class FilterModule(object):
    '''
    Parse strings of the form `foo.bar/myimage:mytag`
    '''

    def filters(self):
        return {
            'parse_docker_image_name': self.parse_docker_image_name
        }

    def parse_docker_image_name (self, docker_image_name, mirrored_base=None):
        if ":" in docker_image_name:
            (uri, tag) = docker_image_name.split(":", 1)
        else:
            uri = docker_image_name
            tag = "latest"

        uri_parts = uri.split("/")
        if len(uri_parts) == 1:
            uri_parts = ["docker.io", "library"] + uri_parts
        elif len(uri_parts) == 2:
            uri_parts = ["docker.io"] + uri_parts
        uri = "/".join(uri_parts)

        shortname = uri_parts[2]

        ret = dict(uri=uri,
                   registry=uri_parts[0], organization=uri_parts[1],
                   shortname=shortname,
                   tag=tag,
                   qualified="%s:%s" % (uri, tag))
        if mirrored_base is not None:
            ret["mirrored"]="%s/%s:%s" % (mirrored_base, shortname, tag)

        return ret
