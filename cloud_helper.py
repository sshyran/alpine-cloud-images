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
    clouds.set_credential_provider(debug=args.debug)

# load build configs
configs = ImageConfigManager(
    conf_path='work/configs/images.conf',
    yaml_path='work/images.yaml',
    log=args.action
)

yaml = YAML()
yaml.explicit_start = True

for image_key in args.image_keys:
    image_config = configs.get(image_key)

    if args.action == 'import':
        clouds.convert_image(image_config)
        clouds.import_image(image_config)
        #clouds.upload_image(image_config)

    elif args.action == 'publish':
        os.makedirs(image_config.local_dir, exist_ok=True)
        artifacts = clouds.publish_image(image_config)
        yaml.dump(artifacts, image_config.artifacts_yaml)
        #clouds.release_image(image_config) # sha256, sign, metadata, put in place for downloading
