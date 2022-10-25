# vim: ts=4 et:

import hashlib
import itertools
import logging
import mergedeep
import os
import pyhocon
import shutil

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from ruamel.yaml import YAML
from subprocess import Popen, PIPE
from urllib.parse import urlparse

import clouds


class ImageConfigManager():

    def __init__(self, conf_path, yaml_path, log=__name__, alpine=None):
        self.conf_path = Path(conf_path)
        self.yaml_path = Path(yaml_path)
        self.log = logging.getLogger(log)
        self.alpine = alpine

        self.now = datetime.utcnow()
        self._configs = {}

        self.yaml = YAML()
        self.yaml.register_class(ImageConfig)
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
        self.log.info('Loading existing %s', self.yaml_path)
        for key, config in self.yaml.load(self.yaml_path).items():
            self._configs[key] = ImageConfig(key, config, log=self.log, yaml=self.yaml)
            # TODO: also pull in additional per-image metatdata from the build process?
        

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
            self._set_version_release(v.strip('"'), vcfg)

        dimensions = list(cfg.Dimensions.keys())
        self.log.debug('dimensions: %s', dimensions)

        for dim_keys in (itertools.product(*cfg['Dimensions'].values())):
            config_key = '-'.join(dim_keys).replace('"', '')

            # dict of dimension -> dimension_key
            dim_map = dict(zip(dimensions, dim_keys))

            # replace version with release, and make image_key from that
            release = cfg.Dimensions.version[dim_map['version']].release
            (rel_map := dim_map.copy())['version'] = release
            image_key = '-'.join(rel_map.values())

            image_config = ImageConfig(
                config_key,
                {
                    'image_key': image_key,
                    'release': release
                } | dim_map,
                log=self.log,
                yaml=self.yaml
            )

            # merge in the Default config
            image_config._merge(cfg.Default)
            skip = False
            # merge in each dimension key's configs
            for dim, dim_key in dim_map.items():
                dim_cfg = deepcopy(cfg.Dimensions[dim][dim_key])

                image_config._merge(dim_cfg)

                # now that we're done with ConfigTree/dim_cfg, remove " from dim_keys
                dim_keys = set(k.replace('"', '') for k in dim_keys)

                # WHEN blocks inside WHEN blocks are considered "and" operations
                while (when := image_config._pop('WHEN', None)):
                    for when_keys, when_conf in when.items():
                        # WHEN keys with spaces are considered "or" operations
                        if len(set(when_keys.split(' ')) & dim_keys) > 0:
                            image_config._merge(when_conf)

                exclude = image_config._pop('EXCLUDE', None)
                if exclude and set(exclude) & set(dim_keys):
                    self.log.debug('%s SKIPPED, %s excludes %s', config_key, dim_key, exclude)
                    skip = True
                    break

                if eol := image_config._get('end_of_life', None):
                    if self.now > datetime.fromisoformat(eol):
                        self.log.warning('%s SKIPPED, %s end_of_life %s', config_key, dim_key, eol)
                        skip = True
                        break

            if skip is True:
                continue

            # merge in the Mandatory configs at the end
            image_config._merge(cfg.Mandatory)

            # clean stuff up
            image_config._normalize()
            image_config.qemu['iso_url'] = self.alpine.virt_iso_url(arch=image_config.arch)

            # we've resolved everything, add tags attribute to config
            self._configs[config_key] = image_config

        self._save_yaml()

    # set current version release
    def _set_version_release(self, v, c):
        info = self.alpine.version_info(v)
        c.put('release', info['release'])
        c.put('end_of_life', info['end_of_life'])

        # release is also appended to name & description arrays
        c.put('name', [c.release])
        c.put('description', [c.release])

    # update current config status
    def refresh_state(self, step, only=[], skip=[], revise=False):
        self.log.info('Refreshing State')
        has_actions = False
        for ic in self._configs.values():
            # clear away any previous actions
            if hasattr(ic, 'actions'):
                delattr(ic, 'actions')

            dim_keys = set(ic.config_key.split('-'))
            if only and len(set(only) & dim_keys) != len(only):
                self.log.debug("%s SKIPPED, doesn't match --only", ic.config_key)
                continue

            if skip and len(set(skip) & dim_keys) > 0:
                self.log.debug('%s SKIPPED, matches --skip', ic.config_key)
                continue

            ic.refresh_state(step, revise)
            if not has_actions and len(ic.actions):
                has_actions = True

        # re-save with updated actions
        self._save_yaml()
        return has_actions


class ImageConfig():
    CONVERT_CMD = {
        'qcow2': ['ln', '-f'],
        'vhd': ['qemu-img', 'convert', '-f', 'qcow2', '-O', 'vpc', '-o', 'force_size=on'],
    }
    # these tags may-or-may-not exist at various times
    OPTIONAL_TAGS = [
        'built', 'uploaded', 'imported', 'import_id', 'import_region', 'published', 'released'
    ]

    def __init__(self, config_key, obj={}, log=None, yaml=None):
        self._log = log
        self._yaml = yaml
        self.config_key = str(config_key)
        tags = obj.pop('tags', None)
        self.__dict__ |= self._deep_dict(obj)
        # ensure tag values are str() when loading
        if tags:
            self.tags = tags

    @classmethod
    def to_yaml(cls, representer, node):
        d = {}
        for k in node.__dict__:
            # don't serialize attributes starting with _
            if k.startswith('_'):
                continue

            d[k] = node.__getattribute__(k)

        return representer.represent_mapping('!ImageConfig', d)

    @property
    def v_version(self):
        return 'edge' if self.version == 'edge' else 'v' + self.version

    @property
    def local_dir(self):
        return Path('work/images') / self.cloud / self.image_key

    @property
    def local_path(self):
        return self.local_dir / 'image.qcow2'

    # TODO? make this metadata_yaml instead, if it contains tags & artifacts?
    @property
    def artifacts_yaml(self):
        return self.local_dir / 'artifacts.yaml'

    @property
    def image_name(self):
        return self.name.format(**self.__dict__)

    @property
    def image_description(self):
        return self.description.format(**self.__dict__)

    @property
    def image_file(self):
        return '.'.join([self.image_name, self.image_format])

    @property
    def image_path(self):
        return self.local_dir / self.image_file

    @property
    def image_metadata_file(self):
        return '.'.join([self.image_name, 'yaml'])

    @property
    def image_metadata_path(self):
        return self.local_dir / self.image_metadata_file

    # TODO: flesh this out to replace upload_url
    @property
    def storage(self):
        if not self._storage:
            s = DictObj({})
            if self.storage_url:
                s.url = urlparse(self.upload_url)

            else:
                # ...
                pass
        
        return self._storage

    @property
    def upload_url(self):
        if not self.upload_path:
            return None

        return '/'.join([self.upload_path, self.image_file]).format(v_version=self.v_version, **self.__dict__)

    @property
    def download_url(self):
        if not self.download_path:
            return None

        return '/'.join([self.download_path, self.image_file]).format(v_version=self.v_version, **self.__dict__)

    # TODO? region_url instead?
    def region_url(self, region, image_id):
        return self.cloud_region_url.format(region=region, image_id=image_id, **self.__dict__)

    def launch_url(self, region, image_id):
        return self.cloud_launch_url.format(region=region, image_id=image_id, **self.__dict__)

    @property
    def tags(self):
        # stuff that really ought to be there
        t = {
            'arch': self.arch,
            'bootstrap': self.bootstrap,
            'cloud': self.cloud,
            'description': self.image_description,
            'end_of_life': self.end_of_life,
            'firmware': self.firmware,
            'image_key': self.image_key,
            'name': self.image_name,
            'project': self.project,
            'release': self.release,
            'revision': self.revision,
            'version': self.version
        }
        # stuff that might not be there yet
        for k in self.OPTIONAL_TAGS:
            if self.__dict__.get(k, None):
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

    def _get(self, attr, default=None):
        return self.__dict__.get(attr, default)

    def _pop(self, attr, default=None):
        return self.__dict__.pop(attr, default)

    # make data ready for Packer ingestion
    def _normalize(self):
        # stringify arrays
        self.name = '-'.join(self.name)
        self.description = ' '.join(self.description)
        self._resolve_motd()
        self._stringify_repos()
        self._stringify_packages()
        self._stringify_services()
        self._stringify_dict_keys('kernel_modules', ',')
        self._stringify_dict_keys('kernel_options', ' ')
        self._stringify_dict_keys('initfs_features', ' ')

    def _resolve_motd(self):
        # merge version/release notes, as apporpriate
        if self.motd.get('version_notes', None) and self.motd.get('release_notes', None):
            if self.version == 'edge':
                # edge is, by definition, not released
                self.motd.pop('version_notes', None)
                self.motd.pop('release_notes', None)

            elif self.release == self.version + '.0':
                # no point in showing the same URL twice
                self.motd.pop('release_notes')

            else:
                # combine version and release notes
                self.motd['release_notes'] = self.motd.pop('version_notes') + '\n' + \
                    self.motd['release_notes']

        # TODO: be rid of null values
        self.motd = '\n\n'.join(self.motd.values()).format(**self.__dict__)

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

    def refresh_state(self, step, revise=False):
        log = self._log
        actions = {}
        revision = 0
        # TODO: local metadata -> stored metadata -> renamed clouds.latest_build_image
        remote_image = clouds.latest_build_image(self)
        log.debug('\n%s', remote_image)
        step_state = step == 'state'

        # TODO: this needs to be sorted out for upload and release targets

        # enable actions based on the specified step
        if step in ['local', 'upload', 'import', 'publish', 'state']:
            actions['build'] = True

        if self.upload_path and step in ['upload', 'import', 'publish', 'state']:
            actions['upload'] = True

        if step in ['import', 'publish', 'state']:
            actions['import'] = True

        if step in ['publish', 'state']:
            # we will resolve publish destinations (if any) later
            actions['publish'] = True

        if revise:
            if self.local_path.exists():
                # remove previously built local image artifacts
                log.warning('%s existing local image dir %s',
                    'Would remove' if step_state else 'Removing',
                    self.local_dir)
                if not step_state:
                    shutil.rmtree(self.local_dir)

            # TODO? if self.uploaded --> self.remove_file(image, metadata, checksums)

            if remote_image and remote_image.published:
                log.warning('%s image revision for %s',
                    'Would bump' if step_state else 'Bumping',
                    self.image_key)
                revision = int(remote_image.revision) + 1

            elif remote_image and remote_image.imported:
                # remove existing imported (but unpublished) image
                log.warning('%s unpublished remote image %s',
                    'Would remove' if step_state else 'Removing',
                    remote_image.import_id)
                if not step_state:
                    clouds.delete_image(self, remote_image.import_id)

            remote_image = None

        elif remote_image:
            if remote_image.imported:
                # already imported, don't build/upload/import again
                log.debug('%s - already imported', self.image_key)
                actions.pop('build', None)
                actions.pop('upload', None)
                actions.pop('import', None)

            if remote_image.published:
                # NOTE: re-publishing can update perms or push to new regions
                log.debug('%s - already published', self.image_key)

        if self.local_path.exists():
            # local image's already built, don't rebuild
            log.debug('%s - already locally built', self.image_key)
            actions.pop('build', None)

        # TODO? if self.uploaded --> already uploaded?

        # merge remote_image data into image state
        if remote_image:
            self.__dict__ |= dict(remote_image)

        else:
            self.__dict__ |= {
                'revision': revision,
                'imported': None,
                'import_id': None,
                'import_region': None,
                'published': None,
            }

        # update artifacts, if we've got 'em
        if self.artifacts_yaml.exists():
            self.artifacts = self.yaml.load(self.artifacts_yaml)
        else:
            self.artifacts = None

        self.actions = list(actions)
        log.info('%s/%s = %s', self.cloud, self.image_name, self.actions)

        self.state_updated = datetime.utcnow().isoformat()

    def _run(self, cmd, errmsg=None, errvals=[]):
        log = self._log
        p = Popen(cmd, stdout=PIPE, stdin=PIPE, encoding='utf8')
        out, err = p.communicate()
        if p.returncode:
            if log:
                if errmsg:
                    log.error(errmsg, *errvals)

                log.error('COMMAND: %s', ' '.join(cmd))
                log.error('EXIT: %d', p.returncode)
                log.error('STDOUT:\n%s', out)
                log.error('STDERR:\n%s', err)

            raise RuntimeError

        return out, err

    def _store_file(self, file):
        log = self._log
        if not self.storage_url:
            log.info('Skipping storage of "%s", storage_url not configured', file)
            return
        
        file_path = self.local_dir / file
        url = self.storage.url
        if url.scheme in ['', 'file']:
            path = Path(url.netloc + url.path).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            log.info('Copying %s to %s', file_path, path)
            shutil.copy2(file_path, path)
            return

        elif url.scheme != 'ssh':
            log.error('Uploading with %s scheme currently unsupported', url.scheme)
            raise RuntimeError

        ssh_port = ['-p', url.port] if url.port else []
        scp_port = ['-P', url.port] if url.port else []
        ssh_user = ['-l', url.username] if url.username else []
        scp_user = url.username + '@' if url.username else ''
        host = url.hostname
        path = Path(url.path[1:])   # drop leading / on urlpath -- use // for absolute path
        log.info('Uploading %s to %s', file_path, self.upload_url)
        self._run(
            ['ssh'] + ssh_port + ssh_user + [host, 'mkdir', '-p', str(path.parent)],
            log, errmsg='Unable to create parent path for %s', errvals=[self.upload_url],
        )
        self._run(
            ['scp'] + scp_port + [str(file_path), scp_user + ':'.join([host, str(path)])],
            log, errmsg='Unable to upload image to %s', errvals=[self.upload_url],
        )

    # TODO: def _retrieve_file(self, file)
    # TODO: def _remove_file(self, file)

    def _save_checksum(self, file):
        self._log.info("Calculating checksum for '%s'", file)
        sha256_hash = hashlib.sha256()
        with open(file, 'rb') as f:
            for block in iter(lambda: f.read(4096), b''):
                sha256_hash.update(block)

        with open(str(file) + '.sha256', 'w') as f:
            print(sha256_hash.hexdigest(), file=f)
        
    # convert local QCOW2 to format appropriate for a cloud
    def convert_image(self):
        self._log.info('Converting %s to %s', self.local_path, self.image_path)
        self._run(
            self.CONVERT_CMD[self.image_format] + [self.local_path, self.image_path],
            errmsg='Unable to convert %s to %s', errvals=[self.local_path, self.image_path],
        )
        self._save_checksum(self.image_path)
        self.built = datetime.utcnow().isoformat()

    def save_metadata(self, upload=True):
        os.makedirs(self.local_dir, exist_ok=True)
        self._log.info('Saving image metadata')
        self.yaml.dump(dict(self.tags), self.image_metadata_path)
        self._save_checksum(self.image_metadata_path)

    def upload_metadata(self):
        self._upload(self.image_metadata_file)

    def upload_image(self):
        self._upload(self.image_file)
        self.uploaded = datetime.utcnow().isoformat()


class DictObj(dict):

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]


class Tags(DictObj):

    def __init__(self, d={}, from_list=None, key_name='Key', value_name='Value'):
        for key, value in d.items():
            self.__setattr__(key, value)

        if from_list:
            self.from_list(from_list, key_name, value_name)

    def __setattr__(self, key, value):
        self[key] = str(value)

    def as_list(self, key_name='Key', value_name='Value'):
        return [{key_name: k, value_name: v} for k, v in self.items()]

    def from_list(self, list=[], key_name='Key', value_name='Value'):
        for tag in list:
            self.__setattr__(tag[key_name], tag[value_name])
