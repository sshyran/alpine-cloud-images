# vim: ts=4 et:

import json
import re
from datetime import datetime, timedelta
from urllib.request import urlopen


class Alpine():

    DEFAULT_RELEASES_URL = 'https://alpinelinux.org/releases.json'
    DEFAULT_CDN_URL = 'https://dl-cdn.alpinelinux.org/alpine'
    DEFAULT_WEB_TIMEOUT = 5

    def __init__(self, releases_url=None, cdn_url=None, web_timeout=None):
        self.now = datetime.utcnow()
        self.release_today = self.now.strftime('%Y%m%d')
        self.eol_tomorrow = (self.now + timedelta(days=1)).strftime('%F')
        self.latest = None
        self.versions = {}
        self.releases_url = releases_url or self.DEFAULT_RELEASES_URL
        self.web_timeout = web_timeout or self.DEFAULT_WEB_TIMEOUT
        self.cdn_url = cdn_url or self.DEFAULT_CDN_URL

        # get all Alpine versions, and their EOL and latest release
        res = urlopen(self.releases_url, timeout=self.web_timeout)
        r = json.load(res)
        branches = sorted(
            r['release_branches'], reverse=True,
            key=lambda x: x.get('branch_date', '0000-00-00')
        )
        for b in branches:
            ver = b['rel_branch'].lstrip('v')
            if not self.latest:
                self.latest = ver

            rel = None
            if releases := b.get('releases', None):
                rel = sorted(
                    releases, reverse=True, key=lambda x: x['date']
                )[0]['version']
            elif ver == 'edge':
                # edge "releases" is today's YYYYMMDD
                rel = self.release_today

            self.versions[ver] = {
                'version': ver,
                'release': rel,
                'end_of_life': b.get('eol_date', self.eol_tomorrow),
                'arches': b.get('arches'),
            }

    def _ver(self, ver=None):
        if not ver or ver == 'latest' or ver == 'latest-stable':
            ver = self.latest

        return ver

    def repo_url(self, repo, arch, ver=None):
        ver = self._ver(ver)
        if ver != 'edge':
            ver = 'v' + ver

        return f"{self.cdn_url}/{ver}/{repo}/{arch}"

    def virt_iso_url(self, arch, ver=None):
        ver = self._ver(ver)
        rel = self.versions[ver]['release']
        return f"{self.cdn_url}/v{ver}/releases/{arch}/alpine-virt-{rel}-{arch}.iso"

    # TODO: maybe we can also get links to version/releases announcments somewhere around here
    def version_info(self, ver=None):
        ver = self._ver(ver)
        if ver not in self.versions:
            # perhaps a release candidate?
            apk_ver = self.apk_version('main', 'x86_64', 'alpine-base', ver=ver)
            rel = apk_ver.split('-')[0]
            ver = '.'.join(rel.split('.')[:2])
            self.versions[ver] = {
                'version': ver,
                'release': rel,
                'end_of_life': self.eol_tomorrow,
                'arches': self.versions['edge']['arches'],  # reasonable assumption
            }

        return self.versions[ver]

    # TODO?  maybe implement apk_info() to read from APKINDEX, but for now
    #   this apk_version() seems faster and gets what we need

    def apk_version(self, repo, arch, apk, ver=None):
        ver = self._ver(ver)
        repo_url = self.repo_url(repo, arch, ver=ver)
        apks_re = re.compile(f'"{apk}-(\\d.*)\\.apk"')
        res = urlopen(repo_url, timeout=self.web_timeout)
        for line in map(lambda x: x.decode('utf8'), res):
            if not line.startswith('<a href="'):
                continue

            match = apks_re.search(line)
            if match:
                return match.group(1)

        # didn't find it?
        raise RuntimeError(f"Unable to find {apk} APK via {repo_url}")
