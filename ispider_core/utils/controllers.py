def reduce_fetch_controller(fetch_controller, lock, dom_tld):
    if dom_tld not in fetch_controller:
        return
    with lock:
        fetch_controller[dom_tld] -= 1
