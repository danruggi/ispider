import multiprocessing

import hashlib
import pathlib
import os
import multiprocessing

from pybloom_live import BloomFilter

from ispider_core.utils.ifiles import get_dump_file_name  # or include get_dump_file_name directly here
from ispider_core.utils.logger import LoggerFactory

from multiprocessing.managers import BaseManager

class SeenFilter:
    def __init__(self, conf, lock, capacity=10_000_000, error_rate=0.001):
        self.conf = conf
        self.lock = lock
        self.bloom = BloomFilter(capacity=capacity, error_rate=error_rate)
        self.logger = LoggerFactory.create_logger("./logs", "seen_filter.log", log_level=conf['LOG_LEVEL'], stdout_flag=True)

        self._load_existing_hashes()

    def _hash_from_req(self, reqA):
        rd = reqA[1]
        url = reqA[0]
        dom_tld = reqA[2]
        path = ""
        try:
            path = get_dump_file_name(rd, url, dom_tld, self.conf)
        except:
            pass
        h = hashlib.sha256(str(path).encode('utf-8')).hexdigest()
        return h

    def _load_existing_hashes(self):
        path_dumps = self.conf['path_dumps']
        for path in pathlib.Path(path_dumps).rglob("*.html"):
            h = hashlib.sha256(str(path).encode('utf-8')).hexdigest()
            with self.lock:
                self.bloom.add(h)

    def bloom_len(self):
        return len(self.bloom)

    def req_in_seen(self, reqA):
        if reqA[1] != 'internal_url':
            return False
        h = self._hash_from_req(reqA)
        with self.lock:
            in_bloom = h in self.bloom
        # self.logger.debug(f"[{h}] {reqA} req_in_seen in bloom: {in_bloom}")
        return in_bloom

    def resp_to_req(self, resp):
        url = resp['url']
        rd = resp['request_discriminator']
        dom_tld = resp['dom_tld']
        reduced_reqA = (url, rd, dom_tld)
        return reduced_reqA

    def add_to_seen_req(self, reqA):
        h = self._hash_from_req(reqA)
        with self.lock:
            self.bloom.add(h)

    def save(self, path):
        with self.lock:
            with open(path, 'wb') as f:
                self.bloom.tofile(f)

    def load(self, path):
        with self.lock:
            with open(path, 'rb') as f:
                self.bloom = BloomFilter.fromfile(f)
