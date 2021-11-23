# vim: ts=4 et:

import itertools
import logging
import mergedeep
import os
import pyhocon
import shutil

from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from ruamel.yaml import YAML

from alpine import get_version_release
import clouds


class ImageConfigManager():

    def __init__(self, conf_path, yaml_path, log=__name__, iso_url_format=None):
        self.conf_path = Path(conf_path)
        self.yaml_path = Path(yaml_path)
        self.log = logging.getLogger(log)
        self.iso_url_format = iso_url_format

        self.now = datetime.utcnow()
        self.tomorrow = self.now + timedelta(days=1)
        self._configs = {}

        self.yaml = YAML()
        self.yaml.register_class(ImageConfig)
        self.yaml.default_flow_style = False
        self.yaml.explicit_start = True
        # hide !ImageConfig tag from Packer
        self.yaml.representer.org_represent_mapping = self.yaml.representer.represent_mapping
        self.yaml.representer.represent_mapping = self._strip_yaml_tag_type

        # load resolved YAML, if exists
        if self.yaml_path.exists():
            self._load_yaml()
        else:
            self._resolve()

    def get(self, key=None):
        if not key:
            return self._configs

        return self._configs[key]

    # load already-resolved YAML configs, restoring ImageConfig objects
    def _load_yaml(self):
        # TODO: no warning if we're being called from cloud_helper.py
        self.log.warning('Loading existing %s', self.yaml_path)
        for key, config in self.yaml.load(self.yaml_path).items():
            self._configs[key] = ImageConfig(key, config)

    # save resolved configs to YAML
    def _save_yaml(self):
        self.log.info('Saving %s', self.yaml_path)
        self.yaml.dump(self._configs, self.yaml_path)

    # hide !ImageConfig tag from Packer
    def _strip_yaml_tag_type(self, tag, mapping, flow_style=None):
        if tag == '!ImageConfig':
            tag = u'tag:yaml.org,2002:map'

        return self.yaml.representer.org_represent_mapping(tag, mapping, flow_style=flow_style)

    # resolve from HOCON configs
    def _resolve(self):
        self.log.info('Generating configs.yaml in work environment')
        cfg = pyhocon.ConfigFactory.parse_file(self.conf_path)
        # set version releases
        for v, vcfg in cfg.Dimensions.version.items():
            # version keys are quoted to protect dots
            self.set_version_release(v.strip('"'), vcfg)

        dimensions = list(cfg.Dimensions.keys())
        self.log.debug('dimensions: %s', dimensions)

        for dim_keys in (itertools.product(*cfg['Dimensions'].values())):
            image_key = '-'.join(dim_keys).replace('"', '')

            # dict of dimension -> dimension_key
            dim_map = dict(zip(dimensions, dim_keys))
            release = cfg.Dimensions.version[dim_map['version']].release
            image_config = ImageConfig(image_key, {'release': release} | dim_map)

            # merge in the Default config
            image_config._merge(cfg.Default)
            skip = False
            # merge in each dimension key's configs
            for dim, dim_key in dim_map.items():
                dim_cfg = deepcopy(cfg.Dimensions[dim][dim_key])
                exclude = dim_cfg.pop('EXCLUDE', None)
                if exclude and set(exclude) & set(dim_keys):
                    self.log.debug('%s SKIPPED, %s excludes %s', image_key, dim_key, exclude)
                    skip = True
                    break

                image_config._merge(dim_cfg)

                # now that we're done with ConfigTree/dim_cfg, remove " from dim_keys
                dim_keys = set(k.replace('"', '') for k in dim_keys)

                # WHEN blocks inside WHEN blocks are considered "and" operations
                while (when := image_config._pop('WHEN', None)):
                    for when_keys, when_conf in when.items():
                        # WHEN keys with spaces are considered "or" operations
                        if len(set(when_keys.split(' ')) & dim_keys) > 0:
                            image_config._merge(when_conf)

            if skip is True:
                continue

            # merge in the Mandatory configs at the end
            image_config._merge(cfg.Mandatory)

            # clean stuff up
            image_config._normalize()
            image_config.qemu['iso_url'] = self.iso_url_format.format(arch=image_config.arch)

            # we've resolved everything, add tags attribute to config
            self._configs[image_key] = image_config

        self._save_yaml()

    # set current version release
    def set_version_release(self, v, c):
        if v == 'edge':
            c.put('release', self.now.strftime('%Y%m%d'))
            c.put('end_of_life', self.tomorrow.strftime('%F'))
        else:
            c.put('release', get_version_release(f"v{v}")['release'])

        # release is also appended to build name array
        c.put('name', [c.release])

    # update current config status
    def determine_actions(self, step, only, skip, revise):
        self.log.info('Determining Actions')
        has_actions = False
        for ic in self._configs.values():
            # clear away any previous actions
            if hasattr(ic, 'actions'):
                delattr(ic, 'actions')

            dim_keys = set(ic.image_key.split('-'))
            if only and len(set(only) & dim_keys) != len(only):
                self.log.debug("%s SKIPPED, doesn't match --only", ic.image_key)
                continue

            if skip and len(set(skip) & dim_keys) > 0:
                self.log.debug('%s SKIPPED, matches --skip', ic.image_key)
                continue

            ic.determine_actions(step, revise)
            if not has_actions and len(ic.actions):
                has_actions = True

        # re-save with updated actions
        self._save_yaml()
        return has_actions


class ImageConfig():

    def __init__(self, image_key, obj={}):
        self.image_key = str(image_key)
        tags = obj.pop('tags', None)
        self.__dict__ |= self._deep_dict(obj)
        # ensure tag values are str() when loading
        if tags:
            self.tags = tags

    @property
    def local_dir(self):
        return os.path.join('work/images', self.name)

    @property
    def local_path(self):
        return os.path.join(self.local_dir, 'image.' + self.local_format)

    @property
    def image_name(self):
        return '-r'.join([self.name, str(self.revision)])

    @property
    def image_description(self):
        return self.description.format(**self.__dict__)

    @property
    def tags(self):
        # stuff that really ought to be there
        t = {
            'arch': self.arch,
            'bootstrap': self.bootstrap,
            'build_name': self.name,
            'build_revision': self.revision,
            'cloud': self.cloud,
            'description': self.image_description,
            'end_of_life': self.end_of_life,
            'firmware': self.firmware,
            'name': self.image_name,
            'release': self.release,
            'version': self.version
        }
        # stuff that might not be there yet
        for k in ['imported', 'published', 'source_id', 'source_region']:
            if k in self.__dict__:
                t[k] = self.__dict__[k]
        return Tags(t)

    # recursively convert a ConfigTree object to a dict object
    def _deep_dict(self, layer):
        obj = deepcopy(layer)
        if isinstance(layer, pyhocon.ConfigTree):
            obj = dict(obj)

        try:
            for key, value in layer.items():
                # some HOCON keys are quoted to preserve dots
                if '"' in key:
                    obj.pop(key)
                    key = key.strip('"')

                # version values were HOCON keys at one point, too
                if key == 'version' and '"' in value:
                    value = value.strip('"')

                obj[key] = self._deep_dict(value)
        except AttributeError:
            pass

        return obj

    def _merge(self, obj={}):
        mergedeep.merge(self.__dict__, self._deep_dict(obj), strategy=mergedeep.Strategy.ADDITIVE)

    def _pop(self, attr, default=None):
        return self.__dict__.pop(attr, default)

    # make data ready for Packer ingestion
    def _normalize(self):
        # stringify arrays
        self.name = '-'.join(self.name)
        self.description = ' '.join(self.description)
        self._stringify_repos()
        self._stringify_packages()
        self._stringify_services()
        self._stringify_dict_keys('kernel_modules', ',')
        self._stringify_dict_keys('kernel_options', ' ')
        self._stringify_dict_keys('initfs_features', ' ')

    def _stringify_repos(self):
        # stringify repos map
        #   <repo>: <tag>   # @<tag> <repo> enabled
        #   <repo>: false   # <repo> disabled (commented out)
        #   <repo>: true    # <repo> enabled
        #   <repo>: null    # skip <repo> entirely
        #   ...and interpolate {version}
        self.repos = "\n".join(filter(None, (
            f"@{v} {r}" if isinstance(v, str) else
            f"#{r}" if v is False else
            r if v is True else None
            for r, v in self.repos.items()
        ))).format(version=self.version)

    def _stringify_packages(self):
        # resolve/stringify packages map
        #   <pkg>: true                 # add <pkg>
        #   <pkg>: <tag>                # add <pkg>@<tag>
        #   <pkg>: --no-scripts         # add --no-scripts <pkg>
        #   <pkg>: --no-scripts <tag>   # add --no-scripts <pkg>@<tag>
        #   <pkg>: false                # del <pkg>
        #   <pkg>: null                 # skip explicit add/del <pkg>
        pkgs = {'add': '', 'del': '', 'noscripts': ''}
        for p, v in self.packages.items():
            k = 'add'
            if isinstance(v, str):
                if '--no-scripts' in v:
                    k = 'noscripts'
                    v = v.replace('--no-scripts', '')
                v = v.strip()
                if len(v):
                    p += f"@{v}"
            elif v is False:
                k = 'del'
            elif v is None:
                continue

            pkgs[k] = p if len(pkgs[k]) == 0 else pkgs[k] + ' ' + p

        self.packages = pkgs

    def _stringify_services(self):
        # stringify services map
        #   <level>:
        #       <svc>: true     # enable <svc> at <level>
        #       <svc>: false    # disable <svc> at <level>
        #       <svc>: null     # skip explicit en/disable <svc> at <level>
        self.services = {
            'enable': ' '.join(filter(lambda x: not x.endswith('='), (
                '{}={}'.format(lvl, ','.join(filter(None, (
                    s if v is True else None
                    for s, v in svcs.items()
                ))))
                for lvl, svcs in self.services.items()
            ))),
            'disable': ' '.join(filter(lambda x: not x.endswith('='), (
                '{}={}'.format(lvl, ','.join(filter(None, (
                    s if v is False else None
                    for s, v in svcs.items()
                ))))
                for lvl, svcs in self.services.items()
            )))
        }

    def _stringify_dict_keys(self, d, sep):
        self.__dict__[d] = sep.join(filter(None, (
            m if v is True else None
            for m, v in self.__dict__[d].items()
        )))

    # TODO? determine_current_state()
    def determine_actions(self, step, revise):
        log = logging.getLogger('build')
        self.revision = 0
        # TODO: be more specific about our parameters
        self.remote_image = clouds.latest_build_image(self)
        actions = {}

        # enable actions based on the specified step
        if step in ['local', 'import', 'publish']:
            actions['build'] = True

        if step in ['import', 'publish']:
            actions['import'] = True

        if step == 'publish':
            # we will resolve publish destinations (if any) later
            actions['publish'] = True

        if revise:
            if os.path.exists(self.local_path):
                # remove previously built local image artifacts
                log.warning('Removing existing local image dir %s', self.local_dir)
                shutil.rmtree(self.local_dir)

            if self.remote_image and 'published' in self.remote_image['tags']:
                log.warning('Bumping build revision for %s', self.name)
                self.revision = int(self.remote_image['tags']['build_revision']) + 1

            elif self.remote_image and 'imported' in self.remote_image['tags']:
                # remove existing imported (but unpublished) image
                log.warning('Removing unpublished remote image %s', self.remote_image['id'])
                # TODO: be more specific?
                clouds.remove_image(self)

            self.remote_image = None

        elif self.remote_image and 'imported' in self.remote_image['tags']:
            # already imported, don't build/import again
            log.warning('Already imported, skipping build/import')
            actions.pop('build', None)
            actions.pop('import', None)

        if os.path.exists(self.local_path):
            log.warning('Already built, skipping build')
            # local image's already built, don't rebuild
            actions.pop('build', None)

        # set at time of import, carries forward when published
        if self.remote_image:
            self.end_of_life = self.remote_image['tags']['end_of_life']
            self.revision = self.remote_image['tags']['build_revision']

        else:
            # default to tomorrow's date if unset
            if 'end_of_life' not in self.__dict__:
                tomorrow = datetime.utcnow() + timedelta(days=1)
                self.end_of_life = tomorrow.strftime('%F')

        self.actions = list(actions)
        log.info('%s/%s-r%s = %s', self.cloud, self.name, self.revision, self.actions)


class Tags(dict):

    def __init__(self, d={}, from_list=None, key_name='Key', value_name='Value'):
        for key, value in d.items():
            self.__setattr__(key, value)

        if from_list:
            self.from_list(from_list, key_name, value_name)

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = str(value)

    def __delattr__(self, key):
        del self[key]

    def pop(self, key, default):
        value = default
        if key in self:
            value = self[key]
            del self[key]

        return value

    def as_list(self, key_name='Key', value_name='Value'):
        return [{key_name: k, value_name: v} for k, v in self.items()]

    def from_list(self, list=[], key_name='Key', value_name='Value'):
        for tag in list:
            self.__setattr__(tag[key_name], tag[value_name])
