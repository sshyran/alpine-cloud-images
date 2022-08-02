# vim: ts=4 et:

from . import aws, nocloud   # , oci, gcp, azure

ADAPTERS = {}


def register(*mods):
    for mod in mods:
        cloud = mod.__name__.split('.')[-1]
        if p := mod.register(cloud):
            ADAPTERS[cloud] = p


register(aws, nocloud)   # , oci, azure, gcp)


# using a credential provider is optional, set across all adapters
def set_credential_provider(debug=False):
    from .identity_broker_client import IdentityBrokerClient
    cred_provider = IdentityBrokerClient(debug=debug)
    for adapter in ADAPTERS.values():
        adapter.cred_provider = cred_provider


### forward to the correct adapter

def latest_build_image(config):
    return ADAPTERS[config.cloud].latest_build_image(
        config.project,
        config.image_key
    )


def convert_image(config):
    return ADAPTERS[config.cloud].convert_image(config)


def import_image(config):
    return ADAPTERS[config.cloud].import_image(config)


def remove_image(config, image_id):
    return ADAPTERS[config.cloud].remove_image(image_id)


def upload_image(config):
    return ADAPTERS[config.cloud].upload_image(config)


def publish_image(config):
    return ADAPTERS[config.cloud].publish_image(config)


def release_image(config):
    return ADAPTERS[config.cloud].release_image(config)