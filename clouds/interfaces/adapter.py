# vim: ts=4 et:


class CloudAdapterInterface:

    def __init__(self, cloud, cred_provider=None):
        self._sdk = None
        self._sessions = {}
        self._clients = {}
        self.cloud = cloud
        self.cred_provider = cred_provider
        self._default_region = None

    @property
    def sdk(self):
        raise NotImplementedError

    @property
    def regions(self):
        raise NotImplementedError

    @property
    def default_region(self):
        raise NotImplementedError

    def credentials(self, region=None):
        raise NotImplementedError

    def session(self, region=None):
        raise NotImplementedError

    def client(self, client, region=None):
        raise NotImplementedError

    # TODO: this needs a new name
    # get information about the latest released image
    def latest_build_image(self, project, image_key):
        raise NotImplementedError

    # TODO: The following things don't need to be implemented (see NoCloud) unless we
    # actually do import/publish images for those cloud providers (like we do for AWS).
    # In the meantime, these stubs should be functionally NOOPs

    # import local image to cloud provider
    def import_image(self, config):
        raise NotImplementedError

    # delete/deregister unpublished image from cloud provider
    def delete_image(self, config, image_id):   # TODO: might we have image id in config?
        raise NotImplementedError

    # publish image to cloud provider regions
    def publish_image(self, config):
        raise NotImplementedError