import os
import re
import json
import pathlib
import hashlib
from urllib.parse import urlparse
from datetime import datetime

from ispider_core.utils import domains

def dump_to_file(c, conf):
    rd = c['request_discriminator']
    depth = c['depth']
    dom_tld = c['dom_tld']
    url = c.get('final_url_raw', c['url'])

    # Create the DOM_TLD DIRECTORY
    path_dumps = os.path.join(conf['path_dumps'], dom_tld)
    d = pathlib.Path(path_dumps)

    os.makedirs(path_dumps, exist_ok=True)
    try:
        dump_fname = get_dump_file_name(rd, url, dom_tld, conf)
    except:
        return False
        
    if c['content'] is None:
        open(dump_fname, 'w').close()
        return False

    if rd == 'sitemap':
        c['sitemap_fname'] = "/".join(dump_fname.split("/")[-2:])
    elif rd == 'internal_url':
        c['fname'] = "/".join(dump_fname.split("/")[-2:])
    elif rd == 'landing_page':
        c['fname'] = "/".join(dump_fname.split("/")[-2:])

    try:
        with open(dump_fname, 'wb') as f:
            f.write(c['content'])
    except:
        return False
    return True


def get_dump_file_name(rd, url, dom_tld, conf):
    path_dumps = os.path.join(conf['path_dumps'], dom_tld)

    if rd == 'landing_page':
        return os.path.join(path_dumps, "_.html")

    elif rd == 'robots':
        return os.path.join(path_dumps, "robots.txt")

    elif rd == 'sitemap':
        url_path = urlparse(url).path.strip('/')
        url_quer = urlparse(url).query.strip('/')
        sub, dom, tld, path = domains.get_url_parts(url)

        if url_path.endswith('.gz'):
            url_path = re.sub(r'\.gz$', '', url_path)

        if not url_path and not url_quer:
            raise Exception(f"Empty Sitemap Name: {url}")

        fn = re.sub(r'[^a-zA-Z0-9.]', '_', f"{sub}_{dom}_{tld}_{url_path}_{url_quer}_").strip("_")
        fn = fn[:200]  # Limit filename length
        return os.path.join(path_dumps, fn)

    elif rd == 'internal_url':
        url_path = urlparse(url).path.strip('/')
        url_quer = urlparse(url).query.strip('/')
        sub, dom, tld, path = domains.get_url_parts(url)

        if not url_path and not url_quer and not sub:
            raise Exception(f"Empty internal_url Name: {url}")

        # Build the base string
        base = f"{sub}_{dom}_{tld}_{url_path}_{url_quer}"
        fn = re.sub(r'[^a-zA-Z0-9._-]', '_', base)  # Safe chars only
        fn = re.sub(r'_+', '_', fn).strip("._ ")

        # Compute the max filename length based on MAX_PATH (typically 260 on Windows)
        MAX_PATH = 250  # Linux/macOS typically much higher
        reserved = len(os.path.abspath(path_dumps)) + len(os.sep) + len("_.html")
        max_len = MAX_PATH - reserved

        # Safely truncate the filename base
        fn = fn[:max_len]

        return os.path.join(path_dumps, f"_{fn}.html")

    raise Exception(f"Unknown request_discriminator: {rd}")


def write_positive_json(resp, conf, mod):
    """Write a successful response metadata to unified_conn_meta.X.json"""
    dump_fname = os.path.join(conf['path_jsons'], f"unified_conn_meta.{mod}.json")
    with open(dump_fname, 'a+') as f:
        json.dump(resp, f)
        f.write('\n')

    if os.path.getsize(dump_fname) > conf['MAX_CRAWL_DUMP_SIZE']:
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        new_name = f"unified_conn_meta.{mod}.{current_time}.json"
        os.replace(dump_fname, os.path.join(conf['path_jsons'], new_name))


def write_negative_json(resp, conf, mod):
    """Write a failed response metadata (no content) to unified_conn_meta.X.json"""
    safe = {k: v for k, v in resp.items() if k != "content"}
    safe["is_downloaded"] = False

    dump_fname = os.path.join(conf['path_jsons'], f"unified_conn_meta.{mod}.json")
    with open(dump_fname, 'a+') as f:
        json.dump(safe, f)
        f.write('\n')

    if os.path.getsize(dump_fname) > conf['MAX_CRAWL_DUMP_SIZE']:
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        new_name = f"unified_conn_meta.{mod}.{current_time}.json"
        os.replace(dump_fname, os.path.join(conf['path_jsons'], new_name))



