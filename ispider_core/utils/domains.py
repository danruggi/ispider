import tldextract
import re

def add_https_protocol(s):
    if not s.startswith('http'):
        s = "https://"+s;
    return s
 
def get_url_parts(s):
    ## ver 20230829
    s = re.sub(r'^http[s]?:\/\/', '', s)
    urlA = s.split("/");
    if len(urlA) > 1:
        s = urlA[0]
        path = "/"+"/".join(urlA[1:])
    else:
        path = "/"
    sub = tldextract.extract(s).subdomain
    dom = tldextract.extract(s).domain
    tld = tldextract.extract(s).suffix
    path = path
    return sub, dom, tld, path
