# utils/state_manager.py
import os
import pickle
import threading
from pathlib import Path
from ispider_core.utils.logger import LoggerFactory

class ResumeState:
    def __init__(self, conf, controller):
        self.conf = conf
        self.ctrl = controller
        self.logger = LoggerFactory.create_logger(conf, "state_manager.log", stdout_flag=True)

    def get_path(self, suffix):
        return Path(self.conf['path_data']) / f"unified_{suffix}.pkl"

    def load_pickle(self, suffix):
        path = self.get_path(suffix)
    
        if path.exists():
            try:
                with open(path, 'rb') as f:
                    data = pickle.load(f)
                length = getattr(data, '__len__', lambda: None)()
                if length == 0:
                    self.logger.warning(f"Loaded {suffix} state, but it contains 0 items.")
                    return None
                self.logger.info(f"Loaded {suffix} state with {length} items.")
                return data
            except Exception as e:
                self.logger.error(f"Error loading {suffix}: {e}")
        else:
            self.logger.warning(f"No resume file for {suffix} at {path}")

        return None

    def resume_all(self):
        # 1. Resume domain stats internals FIRST (includes redirect mappings)
        ds = self.load_pickle('dom_stats')
        if ds is not None:
            try:
                self.ctrl.shared_dom_stats.restore(ds)
                self.logger.info("Restored domain stats including redirect mappings")
            except AttributeError:
                self.logger.warning("DomainStats lacks restore(), skipping stats resume")

        # 2. Resume finished domains (now that redirects are loaded)
        domains = self.load_pickle('dom_stats_finished') or set()
        self.ctrl.dom_tld_finished = domains
        self.logger.info(f"Loaded {len(domains)} finished domains")

        # 3. Resume queues
        qin_items = self.load_pickle('qin') or []
        for itm in qin_items:
            self.ctrl.shared_qin.put(itm)

        qout_items = self.load_pickle('qout') or []
        for itm in qout_items:
            self.ctrl.shared_qout.put(itm)

        # 4. Resume seen filter
        try:
            path = self.get_path('seen')
            self.ctrl.seen_filter.load(path)
            self.logger.info(f"Loaded seen state with {self.ctrl.seen_filter.bloom_len()} items.")
        except Exception as e:
            self.logger.warning(f"Seen filter error, skipping for: {e}")

        return True


class SaveState:
    def __init__(self, conf, controller):
        self.conf = conf
        self.ctrl = controller
        self.logger = LoggerFactory.create_logger(conf, "state_manager.log", stdout_flag=True)
        self.lock = threading.Lock()

    def get_path(self, suffix):
        return Path(self.conf['path_data']) / f"unified_{suffix}.pkl"

    def save_pickle(self, data, suffix):
        base = self.get_path(suffix)
        tmp = base.with_suffix('.pkl.tmp')
        try:
            with open(tmp, 'wb') as f:
                pickle.dump(data, f)
            os.replace(tmp, base)
            self.logger.debug(f"Saved state: {suffix}, {getattr(data, '__len__', lambda: 'n/a')()} items")
        except Exception as e:
            self.logger.error(f"Error saving {suffix}: {e}")

    def save_all(self):
        with self.lock:
            # 1. Domains
            finished = self.ctrl.shared_dom_stats.get_finished_domains()
            self.save_pickle(finished, 'dom_stats_finished')

            # 2. Queues
            qin_items = []
            while not self.ctrl.shared_qin.empty():
                qin_items.append(self.ctrl.shared_qin.get())
            self.save_pickle(qin_items, 'qin')
            for itm in qin_items:
                self.ctrl.shared_qin.put(itm)

            qout_items = []
            while not self.ctrl.shared_qout.empty():
                qout_items.append(self.ctrl.shared_qout.get())
            self.save_pickle(qout_items, 'qout')
            for itm in qout_items:
                self.ctrl.shared_qout.put(itm)

            # 3. Seen filter: use .save(path) method directly
            try:
                path = self.get_path('seen')
                self.ctrl.seen_filter.save(path)
                self.logger.debug(f"Saved seen filter to {path}")
            except Exception as e:
                self.logger.warning(f"Could not save seen filter: {e}")

            # 5. Domain stats internals
            try:
                ds_data = self.ctrl.shared_dom_stats.serialize()  # assumes method returns dict
                self.save_pickle(ds_data, 'dom_stats')
                self.logger.debug(f"Saved ds_data Serialized Stats keys: {ds_data.keys()}")
            except Exception as e:
                self.logger.warning(f"Could not serialize domain stats: {e}")

        return True



