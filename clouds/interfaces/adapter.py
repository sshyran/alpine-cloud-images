# vim: ts=4 et:

import logging

from subprocess import Popen, PIPE


class CloudAdapterInterface:
    CONVERT_CMD = {
        'qcow2': ['ln', '-f'],
        'vhd': ['qemu-img', 'convert', '-f', 'qcow2', '-O', 'vpc', '-o', 'force_size=on'],
    }

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

    # get information about the latest released image
    def latest_build_image(self, project, image_key):
        raise NotImplementedError

    # convert local QCOW2 to format appropriate for a cloud
    def convert_image(self, ic):
        log = logging.getLogger('import')
        local_path = ic.local_path
        image_path = ic.local_dir / ic.image_file

        log.info('Converting %s to %s', image_path, image_path)
        p = Popen(self.CONVERT_CMD[ic.image_format] + [ic.local_path, ic.image_path], stdout=PIPE, stdin=PIPE, encoding='utf8')
        out, err = p.communicate()
        if p.returncode:
            log.error('Unable to convert %s to %s format (%s)', ic.local_path, ic.image_path, p.returncode)
            log.error('EXIT: %d', p.returncode)
            log.error('STDOUT:\n%s', out)
            log.error('STDERR:\n%s', err)
            raise RuntimeError

    # import local image to cloud provider
    def import_image(self, config):
        raise NotImplementedError

    # remove unpublished image from cloud provider
    def remove_image(self, config, image_id):
        raise NotImplementedError

    # upload cloud image for testing, if upload_path
    def upload_image(self, config):
        raise NotImplementedError
        # TODO: implement here

    # publish image to cloud provider regions
    def publish_image(self, config):
        raise NotImplementedError

    # generate image checksum, save metadata, sign image, make downloadable, if download_path
    def release_image(self, config):
        raise NotImplementedError
        # TODO: implement here!