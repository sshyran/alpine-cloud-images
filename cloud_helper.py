#!/usr/bin/env python3
# vim: ts=4 et:

# Ensure we're using the Python virtual env with our installed dependencies
import os
import sys
import textwrap

NOTE = textwrap.dedent("""
    This script is meant to be run as a Packer post-processor, and Packer is only
    meant to be executed from the main 'build' script, which is responsible for
    setting up the work environment.
    """)

sys.pycache_prefix = 'work/__pycache__'

if not os.path.exists('work'):
    print('FATAL: Work directory does not exist.', file=sys.stderr)
    print(NOTE, file=sys.stderr)
    exit(1)

# Re-execute using the right virtual environment, if necessary.
venv_args = [os.path.join('work', 'bin', 'python3')] + sys.argv
if os.path.join(os.getcwd(), venv_args[0]) != sys.executable:
    print("Re-executing with work environment's Python...\n", file=sys.stderr)
    os.execv(venv_args[0], venv_args)

# We're now in the right Python environment

import argparse
import logging
from pathlib import Path
from ruamel.yaml import YAML

import clouds
from image_configs import ImageConfigManager


### Constants & Variables

ACTIONS = ['import', 'publish']
LOGFORMAT = '%(name)s - %(levelname)s - %(message)s'


### Functions

# TODO? be more specific with args?
# import image config's local image to cloud
def import_image(ic):
    imported = clouds.import_image(ic)
    # write imported metadata
    imported_yaml = Path(os.path.join(ic.local_dir, 'imported.yaml'))
    yaml.dump(imported, imported_yaml)


# TODO? be more specific with args?
# publish image config's imported image to target regions with expected permissions
def publish_image(ic):
    published = clouds.publish_image(ic)
    # ensure image work directory exists
    os.makedirs(ic.local_dir, exist_ok=True)
    # write published metadata
    published_yaml = Path(os.path.join(ic.local_dir, 'published.yaml'))
    yaml.dump(published, published_yaml)


### Command Line & Logging

parser = argparse.ArgumentParser(description=NOTE)
parser.add_argument('--debug', action='store_true', help='enable debug output')
parser.add_argument(
    '--use-broker', action='store_true',
    help='use the identity broker to get credentials')
parser.add_argument('action', choices=ACTIONS)
parser.add_argument('image_keys', metavar='IMAGE_KEY', nargs='+')
args = parser.parse_args()

log = logging.getLogger(args.action)
log.setLevel(logging.DEBUG if args.debug else logging.INFO)
# log to STDOUT so that it's not all red when executed by packer
console = logging.StreamHandler(sys.stdout)
console.setFormatter(logging.Formatter(LOGFORMAT))
log.addHandler(console)
log.debug(args)

# set up credential provider, if we're going to use it
if args.use_broker:
    clouds.set_credential_provider()

# load build configs
configs = ImageConfigManager(
    conf_path='work/configs/images.conf',
    yaml_path='work/images.yaml',
    log=args.action
)

yaml = YAML()
yaml.default_flow_style = False

for image_key in args.image_keys:
    image_config = configs.get(image_key)

    if args.action == 'import':
        import_image(image_config)

    elif args.action == 'publish':
        publish_image(image_config)
