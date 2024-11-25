import re

class FilterModule(object):
    '''
    Parse a string of the form `foo.bar/myimage:mytag`
    '''

    def filters(self):
        return {
            'parse_external_docker_tag': self.parse_external_docker_tag
        }

    def parse_external_docker_tag(self, docker_tag, mirrored_base=None):
        if ":" in docker_tag:
            (uri, tag) = docker_tag.split(":", 1)
        else:
            uri = docker_tag
            tag = "latest"

        uri_parts = uri.split("/")
        if len(uri_parts) == 1:
            uri_parts = ["docker.io", "library"] + uri_parts
        elif len(uri_parts) == 2:
            uri_parts = ["docker.io"] + uri_parts
        uri = "/".join(uri_parts)

        shortname = uri_parts[-1]

        ret = dict(shortname=shortname, uri=uri, tag=tag,
                    qualified="%s:%s" % (uri, tag))
        if mirrored_base is not None:
            ret["mirrored"]="%s/%s:%s" % (mirrored_base, shortname, tag)

        return ret
