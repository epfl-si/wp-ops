"""Jinja filters that massage Docker registry addresses etc."""


def docker_registry_path_qualified(image_name, namespace, tag="latest"):
    return "docker-registry.default.svc:5000/%s/%s:%s" % (
        namespace, image_name, tag)


class FilterModule(object):
    def filters(self):
        return {
            'docker_registry_path_qualified':  docker_registry_path_qualified
        }
