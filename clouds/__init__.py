# vim: ts=4 et:

from . import aws   # , oci, gcp, azure

ADAPTERS = {}


def register(*mods):
    for mod in mods:
        cloud = mod.__name__.split('.')[-1]
        if p := mod.register(cloud):
            ADAPTERS[cloud] = p


register(aws)   # , oci, azure, gcp)


# using a credential provider is optional, set across all adapters
def set_credential_provider():
    from .identity_broker_client import IdentityBrokerClient
    cred_provider = IdentityBrokerClient()
    for adapter in ADAPTERS.values():
        adapter.cred_provider = cred_provider


### forward to the correct adapter

def latest_build_image(config):
    return ADAPTERS[config.cloud].latest_build_image(config.name)


def import_image(config):
    return ADAPTERS[config.cloud].import_image(config)


def remove_image(config):
    return ADAPTERS[config.cloud].remove_image(config.remote_image['id'])


def publish_image(config):
    return ADAPTERS[config.cloud].publish_image(config)
