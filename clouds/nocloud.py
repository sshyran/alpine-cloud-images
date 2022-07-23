# NOTE: not meant to be executed directly
# vim: ts=4 et:

import logging
import hashlib
import os
import time

from datetime import datetime
from subprocess import Popen, PIPE, run

from .interfaces.adapter import CloudAdapterInterface
from image_configs import Tags, DictObj


# For NoCloud, this will mostly be a no-op.

class NoCloudAdapter(CloudAdapterInterface):
    IMAGE_INFO = [
        'revision', 'imported', 'import_id', 'import_region', 'published',
    ]

    # get the latest imported image for a given build name
    def latest_build_image(self, project, image_key):
        # TODO: get info from permanently published image (if exists)
        return None

    # import an image
    def import_image(self, ic):
        # TODO: upload to temporary location
        # TODO: what exactly should be returned?
        return DictObj({
            'revision': ic.revision,
            'imported': datetime.now(),
            'import_id': 'url?',
        })

    # remove an (unpublished) image
    def remove_image(self, image_id):
        # TODO: remove image from temporary location
        pass

    # publish an image
    def publish_image(self, ic):
        # TODO: move image from temporary to permanent location
        # TODO: what exaclty should be returned?
        return {
            'generic?':  'url?'
        }


def register(cloud, cred_provider=None):
    return NoCloudAdapter(cloud, cred_provider)
