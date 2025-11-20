from ispider_core import ISpider
import pandas as pd

if __name__ == '__main__':
    config_overrides = {
        'USER_FOLDER': '/Volumes/Sandisk2TB/test_business_scraper_26',
        'POOLS': 32,
        'ASYNC_BLOCK_SIZE': 8,
        'MAXIMUM_RETRIES': 1,
        'CODES_TO_RETRY': [430, 503, 500, 429, -1],
        'CURL_INSECURE': True,
        'MAX_PAGES_POR_DOMAIN': 100000,
        'ENGINES': ['httpx', 'curl'],
        'LOG_LEVEL': 'DEBUG',
        'CRAWL_METHODS': [],
    }

    df = pd.read_csv('t.csv')
    # df = df.sample(n=10, random_state=42)  # random_state for reproducibility

    doms = df['dom_tld'].tolist()
    print(doms)
    # doms = ['deskydoo.com']
    # doms = []
    with ISpider(domains=doms, stage="unified", **config_overrides) as spider:
        spider.run()
    
    