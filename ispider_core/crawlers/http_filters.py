import re
import os
from urllib.parse import urlparse

from ispider_core.utils import ifiles

def filter_on_resp(c):
    if 'request_discriminator' not in c or 'status_code' not in c:
        raise Exception("Missing request request_discriminator or status_code")

    ## Sitemap crawling mapped errors
    if c['request_discriminator'] == 'sitemap':
        if 'final_url_raw' not in c:
            raise Exception(f"FILTER102: [{c['status_code']}] No final_url in sitemap call")
        
        furl = c['final_url_raw']
        
        url_path = urlparse(furl).path.strip('/')
        if url_path == "" or not re.search(r'[0-9a-zA-Z]', url_path):
            raise Exception("FILTER101: Sitemap redirecting to /")

    return True

def filter_file_exists(resp, conf):
    url = resp['url']
    rd = resp['request_discriminator']
    dom_tld = resp['dom_tld']

    if rd != 'internal_url':
        return True

    dfA = list()
    try:
        if 'final_url_raw' in resp:
            furl = resp['final_url_raw']
            l = ifiles.get_dump_file_name(rd, furl, dom_tld, conf)
            dfA.append(l)
    except:
        pass

    l = ""
    try:
        l = ifiles.get_dump_file_name(rd, url, dom_tld, conf)
    except:
        pass

    if os.path.isfile(l):
        raise Exception(f"** OUTFILE EXISTS -- {str(rd)} -- {str(l)}");

    return True


