#!/usr/bin/env python3
# vim: ts=4 et:

# Ensure we're using the Python virtual env with our installed dependencies
import os
import sys
import textwrap

NOTE = textwrap.dedent("""
    This script's output is compatible with the retired alpine-ec2-ami repo's
    releases/alpine.yaml, in order to bridge the gap until
    https://alpinelinux.org/cloud dynamically calls a published-image metadata
    service.  This script should only be run after the main 'build' script has
    been used successfully to publish ALL images, and the STDOUT should be
    committed to the https://gitlab.alpinelinux.org/alpine/infra/alpine-mksite
    repo as 'cloud/releases-in.yaml'.
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

from collections import defaultdict
from ruamel.yaml import YAML

import clouds
from image_configs import ImageConfigManager


### Constants & Variables

LOGFORMAT = '%(name)s - %(levelname)s - %(message)s'


### Functions

# allows us to set values deep within an object that might not be fully defined
def dictfactory():
    return defaultdict(dictfactory)


# undo dictfactory() objects to normal objects
def undictfactory(o):
    if isinstance(o, defaultdict):
        o = {k: undictfactory(v) for k, v in o.items()}
    return o


### Command Line & Logging

parser = argparse.ArgumentParser(description=NOTE)
parser.add_argument(
    '--use-broker', action='store_true',
    help='use the identity broker to get credentials')
parser.add_argument('--debug', action='store_true', help='enable debug output')
args = parser.parse_args()

log = logging.getLogger('gen_releases')
log.setLevel(logging.DEBUG if args.debug else logging.INFO)
console = logging.StreamHandler(sys.stderr)
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
    log='gen_releases'
)
# make sure images.yaml is up-to-date with reality
configs.refresh_state('final')

yaml = YAML()

releases = dictfactory()
for i_key, i_cfg in configs.get().items():
    release = i_cfg.version if i_cfg.version == 'edge' else i_cfg.release
    releases[release][i_key][i_cfg.tags.name] = dict(i_cfg.tags) | {
        'creation_date': i_cfg.published,
        'artifacts': i_cfg.artifacts,
    }

yaml.dump(undictfactory(releases), sys.stdout)
