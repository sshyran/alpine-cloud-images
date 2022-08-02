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

    def latest_build_image(self, project, image_key):
        raise NotImplementedError

    def import_image(self, config):
        raise NotImplementedError

    def remove_image(self, config, image_id):
        raise NotImplementedError

    def publish_image(self, config):
        raise NotImplementedError
