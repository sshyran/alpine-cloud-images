# vim: ts=4 et:

import re
from urllib.request import urlopen


# constants and vars
CDN_URL = 'https://dl-cdn.alpinelinux.org/alpine'


# TODO:  also get EOL from authoritative source

def get_version_release(alpine_version):
    apk_ver = get_apk_version(alpine_version, 'main', 'x86_64', 'alpine-base')
    release = apk_ver.split('-')[0]
    version = '.'.join(release.split('.')[:2])
    return {'version': version, 'release': release}


# TODO?  maybe download and parse APKINDEX instead?
# also check out https://dl-cdn.alpinelinux.org/alpine/v3.15/releases/x86_64/latest-releases.yaml
def get_apk_version(alpine_version, repo, arch, apk):
    repo_url = f"{CDN_URL}/{alpine_version}/{repo}/{arch}"
    apks_re = re.compile(f'"{apk}-(\\d.*)\\.apk"')
    res = urlopen(repo_url)
    for line in map(lambda x: x.decode('utf8'), res):
        if not line.startswith('<a href="'):
            continue

        match = apks_re.search(line)
        if match:
            return match.group(1)

    # didn't find it?
    raise RuntimeError(f"Unable to find {apk} APK via {repo_url}")
