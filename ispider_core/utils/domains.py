
def add_https_protocol(s):
    if not s.startswith('http'):
        s = "https://"+s;

    return s
 
