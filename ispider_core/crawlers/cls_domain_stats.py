import queue

class SharedDomainStats:
    def __init__(self, manager, lock, qstats=None):
        self.lock = lock
        self.qstats = qstats
        self.local_stats = dict()
        self.dom_missing = manager.dict()
        self.dom_total = manager.dict()
        self.dom_last_call = manager.dict()
        self.dom_engine = manager.dict()

    def add_domain(self, dom_tld):
        self.dom_missing[dom_tld] = 0
        self.dom_total[dom_tld] = 0
        self.dom_last_call[dom_tld] = 0
        self.dom_engine[dom_tld] = None
        self.local_stats[dom_tld] = {}

    def reduce_missing(self, dom_tld):
        if dom_tld not in self.dom_missing:
            return
        with self.lock:
            self.dom_missing[dom_tld] -= 1

    def add_missing_total(self, dom_tld):
        if dom_tld not in self.dom_missing:
            return
        if dom_tld not in self.dom_total:
            return
        with self.lock:
            self.dom_missing[dom_tld] += 1
            self.dom_total[dom_tld] += 1

    def get_finished_domains(self):
        return [k for k, v in self.dom_missing.items() if v == 0]

    def get_unfinished_domains(self):
        return [k for k, v in self.dom_missing.items() if v > 0]

    def get_total_pages(self, dom_tld):
        return self.dom_total[dom_tld]

    def get_tot_domains(self):
        return len(self.dom_missing)

    def count_by(self, condition_fn):
        return sum(1 for v in self.dom_missing.values() if condition_fn(v))

    def get_sorted_missing(self, reverse=True):
        return dict(sorted(self.dom_missing.items(), key=lambda item: item[1], reverse=reverse))
        
    def filter_and_add_links(self, dom_tld, links, max_pages):
        """Filter links to avoid exceeding max_pages, and update counters safely."""
        with self.lock:
            if dom_tld not in self.dom_missing:
                self.add_domain(dom_tld)

            current_total = self.dom_total.get(dom_tld, 0)
            remaining = max_pages - current_total

            if remaining <= 0:
                return []  # No room left

            limited_links = links[:remaining]
            count = len(limited_links)

            self.dom_total[dom_tld] += count
            self.dom_missing[dom_tld] += count

            return limited_links

    def flush_qstats(self):
        """Pull all items from qstats and aggregate into local_stats."""
        if not self.qstats:
            return

        try:
            while True:
                item = self.qstats.get_nowait()
                dom_tld = item["dom_tld"]
                k = item["key"]
                v = item["value"]
                op = item.get("op", "sum")  # Default to sum if not specified

                if dom_tld not in self.local_stats:
                    self.local_stats[dom_tld] = {}

                if op == "sum":
                    # Initialize to 0 if not yet set
                    if k not in self.local_stats[dom_tld]:
                        self.local_stats[dom_tld][k] = 0
                    self.local_stats[dom_tld][k] += v
                elif op == "set":
                    # Just set/overwrite
                    self.local_stats[dom_tld][k] = v
                else:
                    # Optional: warn or ignore unknown op
                    pass

        except queue.Empty:
            pass