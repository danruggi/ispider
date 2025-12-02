from collections import defaultdict, deque, Counter
from heapq import heapify, heappop, heappush

import time

def sparse_q_elements_with_timing(A, domain_last_seen, min_delay=0.5):
    """
    Sparsing that considers timing between same-domain requests.
    Ensures domains are separated by at least min_delay seconds.
    Randomness if more elements of the same domain in queue... it works, but not works
    To be improved
    """
    if not A:
        return A
    
    tdict = {}
    for el in A:
        dom_tld = el[2]
        tdict.setdefault(dom_tld, []).append(el)
    
    # Sort domains by last seen time (least recent first)
    current_time = time.time()
    domains_by_readiness = []
    
    for dom_tld in tdict.keys():
        last_seen = domain_last_seen.get(dom_tld, 0)
        time_since_last = current_time - last_seen
        
        # Priority: domains not seen recently get processed first
        priority = time_since_last if time_since_last < min_delay else min_delay
        domains_by_readiness.append((priority, dom_tld))
    
    domains_by_readiness.sort(reverse=True)
    
    # Build output with maximum separation
    out = []
    used_domains = set()
    
    # First pass: one URL from each domain
    for _, dom_tld in domains_by_readiness:
        if tdict[dom_tld]:
            out.append(tdict[dom_tld].pop(0))
            used_domains.add(dom_tld)
    
    # Second pass: distribute remaining URLs
    while any(tdict.values()):
        for _, dom_tld in domains_by_readiness:
            if tdict[dom_tld]:
                out.append(tdict[dom_tld].pop(0))
    
    return out

## Leave some elements in the queue?
def spread_domains_balanced(dom_list):
    freq = Counter(dom_list)
    heap = [(-cnt, dom) for dom, cnt in freq.items()]
    heapify(heap)

    prev = None
    result = []

    while heap:
        cnt, dom = heappop(heap)
        result.append(dom)
        cnt += 1  # reduce magnitude

        if prev:
            heappush(heap, prev)

        prev = (cnt, dom) if cnt < 0 else None

    return result


def sparse_q_elements(A):
    tdict = defaultdict(deque)
    all_dom_tld = []

    # Fill buckets
    for el in A:
        dom_tld = el[2]
        tdict[dom_tld].append(el)
        all_dom_tld.append(dom_tld)

    spreaded = spread_domains_balanced(all_dom_tld)

    out = []
    for dom_tld in spreaded:
        bucket = tdict[dom_tld]
        if bucket:
            out.append(bucket.popleft())

    return out