import queue
from datetime import datetime 

class SharedDomainStats:
    def __init__(self, manager, logger, lock, qstats=None):
        self.lock = lock
        self.qstats = qstats
        self.local_stats = dict()
        self.dom_missing = manager.dict()
        self.dom_total = manager.dict()
        self.dom_last_call = manager.dict()
        self.dom_engine = manager.dict()
        self.dom_redirects = manager.dict()
        self.logger = logger
        

    def register_redirect(self, original_dom_tld, final_dom_tld):
        """Register a domain redirect and transfer stats to final domain"""
        if original_dom_tld == final_dom_tld:
            return final_dom_tld
            
        with self.lock:
            # Store the redirect mapping
            self.dom_redirects[original_dom_tld] = final_dom_tld
            
            # Initialize final domain if needed
            if final_dom_tld not in self.dom_missing:
                self.add_domain(final_dom_tld)
            
            # Transfer stats from original to final domain
            if original_dom_tld in self.dom_missing:
                # Transfer missing and total counts
                self.dom_missing[final_dom_tld] = (
                    self.dom_missing.get(final_dom_tld, 0) + 
                    self.dom_missing.get(original_dom_tld, 0)
                )
                self.dom_total[final_dom_tld] = (
                    self.dom_total.get(final_dom_tld, 0) + 
                    self.dom_total.get(original_dom_tld, 0)
                )
                
                # Transfer local_stats if they exist
                if original_dom_tld in self.local_stats:
                    if final_dom_tld not in self.local_stats:
                        self.local_stats[final_dom_tld] = {}
                    # Merge stats (sum numeric values, keep other values from original)
                    for key, value in self.local_stats[original_dom_tld].items():
                        if isinstance(value, (int, float)):
                            self.local_stats[final_dom_tld][key] = (
                                self.local_stats[final_dom_tld].get(key, 0) + value
                            )
                        else:
                            self.local_stats[final_dom_tld][key] = value
                
                # REMOVE original domain from all tracking dicts
                del self.dom_missing[original_dom_tld]
                del self.dom_total[original_dom_tld]
                if original_dom_tld in self.dom_last_call:
                    del self.dom_last_call[original_dom_tld]
                if original_dom_tld in self.dom_engine:
                    del self.dom_engine[original_dom_tld]
                if original_dom_tld in self.local_stats:
                    del self.local_stats[original_dom_tld]
                
                self.logger.info(f"Redirect registered: {original_dom_tld} -> {final_dom_tld}")
        
        return final_dom_tld
    
    def get_final_domain(self, dom_tld):
        """Get the final domain after following redirects"""
        return self.dom_redirects.get(dom_tld, dom_tld)

    def serialize(self) -> dict:
        """Return a serializable dict of the current state."""
        with self.lock:
            return {
                "dom_missing": dict(self.dom_missing),
                "dom_total": dict(self.dom_total),
                "dom_last_call": {
                    k: v.isoformat() if v is not None else None
                    for k, v in dict(self.dom_last_call).items()
                },
                "dom_engine": dict(self.dom_engine),
                "dom_redirects": dict(self.dom_redirects),  # NEW
                "local_stats": dict(self.local_stats),
            }

    def restore(self, state: dict):
        """Restore the state from a previously saved dict."""
        with self.lock:
            self.dom_missing.clear()
            self.dom_total.clear()
            self.dom_last_call.clear()
            self.dom_engine.clear()
            self.dom_redirects.clear()  # NEW
            self.local_stats.clear()

            for k, v in state.get("dom_missing", {}).items():
                self.dom_missing[k] = v
            for k, v in state.get("dom_total", {}).items():
                self.dom_total[k] = v
            for k, v in state.get("dom_last_call", {}).items():
                self.dom_last_call[k] = datetime.fromisoformat(v) if v is not None else None
            for k, v in state.get("dom_engine", {}).items():
                self.dom_engine[k] = v
            for k, v in state.get("dom_redirects", {}).items():  # NEW
                self.dom_redirects[k] = v
            for k, v in state.get("local_stats", {}).items():
                self.local_stats[k] = v

    def add_domain(self, dom_tld):
        self.dom_missing[dom_tld] = 0
        self.dom_total[dom_tld] = 0
        self.dom_last_call[dom_tld] = None
        self.dom_engine[dom_tld] = None
        self.local_stats[dom_tld] = {}

    def reduce_missing(self, dom_tld):
        with self.lock:
            if dom_tld not in self.dom_missing:
                return
            self.dom_missing[dom_tld] -= 1

    def reduce_total(self, dom_tld):
        if dom_tld not in self.dom_missing:
            return
        with self.lock:
            self.dom_total[dom_tld] -= 1

    def add_missing_total(self, dom_tld):
        if dom_tld not in self.dom_missing:
            return
        if dom_tld not in self.dom_total:
            return
        with self.lock:
            self.dom_missing[dom_tld] += 1
            self.dom_total[dom_tld] += 1

    def set_last_call(self, dom_tld):
        if dom_tld not in self.dom_last_call:
            return
        with self.lock:
            self.dom_last_call[dom_tld] = datetime.now()

    def is_domain_finished(self, dom_tld):
        """Check if a domain (or its redirect target) is finished"""
        final_dom = self.get_final_domain(dom_tld)
        with self.lock:
            return self.dom_missing.get(final_dom, -1) == 0

    def get_finished_domains(self):
        """Returns all finished domains, including original names that redirected"""
        finished = []
        with self.lock:
            # Get directly finished domains
            finished = [k for k, v in self.dom_missing.items() if v == 0]
            
            # Add reverse mappings: if final domain is finished, original is too
            reverse_redirects = {}
            for orig, final in self.dom_redirects.items():
                if final not in reverse_redirects:
                    reverse_redirects[final] = []
                reverse_redirects[final].append(orig)
            
            # Add original domains whose final destination is finished
            for final_dom in finished:
                if final_dom in reverse_redirects:
                    finished.extend(reverse_redirects[final_dom])
        
        return list(set(finished))  # Remove duplicates

    def get_unfinished_domains(self):
        return [k for k, v in self.dom_missing.items() if v > 0]

    def get_tot_domains(self):
        return len(self.dom_missing)

    def count_by(self, condition_fn):
        return sum(1 for v in self.dom_missing.values() if condition_fn(v))

    def get_sorted_missing(self, reverse=True):
        return dict(sorted(self.dom_missing.items(), key=lambda item: item[1], reverse=reverse))
    
    def increase_script_counters(self, rd, script_controller):
        """
        Increment the unified counters (landings/robots/sitemaps/internal_urls)
        in a multiprocessing-safe way using the shared lock.
        """
        with self.lock:
            if rd == "landing_page":
                script_controller["landings"] = script_controller.get("landings", 0) + 1
            elif rd == "robots":
                script_controller["robots"] = script_controller.get("robots", 0) + 1
            elif rd == "sitemap":
                script_controller["sitemaps"] = script_controller.get("sitemaps", 0) + 1
            elif rd == "internal_url":
                script_controller["internal_urls"] = script_controller.get("internal_urls", 0) + 1
                
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

            # print(f"[DOMSTATS] {dom_tld}: total={self.dom_total[dom_tld]} missing={self.dom_missing[dom_tld]} adding={count}")

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

                # print(item)
                
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