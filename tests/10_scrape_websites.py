import os, sys
import json
import pandas as pd
import numpy as np

import asyncio

from itertools import repeat

import multiprocessing as mp


from ispider_core import ISpider


FILE_GOOGLE ='tests/06_google_search.csv'


if __name__ == '__main__':


    dff05 = pd.read_csv(FILE_GOOGLE)
    doms = dff05['url'].to_list()[:40]
    # doms = dff05['url'].to_list()

    data = ISpider(domains=doms, stage="stage2").run()

