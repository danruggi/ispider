from ispider_core import ISpider
import pandas as pd

if __name__ == '__main__':
    config_overrides = {
        'USER_FOLDER': '/Volumes/Sandisk2TB/test_business_scraper_10',
        'POOLS': 8,
        'ASYNC_BLOCK_SIZE': 16,
        'MAXIMUM_RETRIES': 2,
        'CRAWL_METHODS': [],
        'CODES_TO_RETRY': [430, 503, 500, 429, -1],
        'CURL_INSECURE': True,
        'ENGINES': ['seleniumbase']
    }

    df = pd.read_csv('t.csv')
    doms = df['dom_tld'].tolist()

    ISpider(domains=doms, stage="crawl", **config_overrides).run()
    ISpider(domains=doms, stage="spider", **config_overrides).run()