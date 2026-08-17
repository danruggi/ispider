import hashlib
import json
import os

"""
Optional cross-run cache for sitemap responses, enabled via
conf['SITEMAP_CACHE_ENABLED']. Stores each sitemap's ETag/Last-Modified
plus a copy of its body under <base>/<dom_tld>/.sitemap_cache/, keyed by a
hash of the requested URL (independent of the on-disk dump naming, which
can shift if a sitemap URL redirects).

<base> is conf['SITEMAP_CACHE_DIR'] if set, otherwise conf['path_dumps'].
Callers whose path_dumps is regenerated every run (e.g. a randomized
USER_FOLDER per test run) should set SITEMAP_CACHE_DIR to a fixed,
persistent directory - otherwise the cache never survives to the next run.

On the next run, a cached validator is only used if the cached body file
is still present - otherwise a full GET is forced, since a 304 with
nothing to fall back on would lose the sitemap's links.
"""

CACHE_DIRNAME = ".sitemap_cache"
INDEX_FILENAME = "index.json"


def _cache_base(conf):
    return conf.get('SITEMAP_CACHE_DIR') or conf['path_dumps']


def _cache_dir(dom_tld, conf):
    return os.path.join(_cache_base(conf), dom_tld, CACHE_DIRNAME)


def _index_path(dom_tld, conf):
    return os.path.join(_cache_dir(dom_tld, conf), INDEX_FILENAME)


def _blob_path(dom_tld, conf, url):
    key = hashlib.sha1(url.encode('utf-8')).hexdigest()
    return os.path.join(_cache_dir(dom_tld, conf), f"{key}.body")


def _load_index(dom_tld, conf):
    try:
        with open(_index_path(dom_tld, conf), 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_index(dom_tld, conf, index):
    try:
        os.makedirs(_cache_dir(dom_tld, conf), exist_ok=True)
        with open(_index_path(dom_tld, conf), 'w') as f:
            json.dump(index, f)
    except Exception:
        pass


def get_conditional_headers(url, dom_tld, conf):
    """Conditional-GET headers for a sitemap URL, or {} if there's nothing
    cached (or unsafe) to validate against - which forces a normal fetch."""
    if not conf.get('SITEMAP_CACHE_ENABLED', False):
        return {}

    entry = _load_index(dom_tld, conf).get(url)
    if not entry:
        return {}

    if not os.path.isfile(_blob_path(dom_tld, conf, url)):
        return {}

    headers = {}
    if entry.get('etag'):
        headers['If-None-Match'] = entry['etag']
    if entry.get('last_modified'):
        headers['If-Modified-Since'] = entry['last_modified']
    return headers


def read_cached_body(url, dom_tld, conf):
    try:
        with open(_blob_path(dom_tld, conf, url), 'rb') as f:
            return f.read()
    except Exception:
        return None


def store(url, dom_tld, conf, content, etag, last_modified):
    """Persist a freshly downloaded sitemap body plus its validators, so a
    future run can send a conditional GET for this URL."""
    if not conf.get('SITEMAP_CACHE_ENABLED', False):
        return
    if not etag and not last_modified:
        return
    if content is None:
        return

    try:
        os.makedirs(_cache_dir(dom_tld, conf), exist_ok=True)
        with open(_blob_path(dom_tld, conf, url), 'wb') as f:
            f.write(content)

        index = _load_index(dom_tld, conf)
        index[url] = {'etag': etag, 'last_modified': last_modified}
        _save_index(dom_tld, conf, index)
    except Exception:
        pass
