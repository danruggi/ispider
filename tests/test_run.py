from ispider_core import ISpider
import pandas as pd

if __name__ == '__main__':
    config_overrides = {
        'USER_FOLDER': '/Volumes/Sandisk2TB/test_business_scraper_24',
        'POOLS': 32,
        'ASYNC_BLOCK_SIZE': 8,
        'MAXIMUM_RETRIES': 2,
        'CODES_TO_RETRY': [430, 503, 500, 429, -1],
        'CURL_INSECURE': True,
        'MAX_PAGES_POR_DOMAIN': 50000,
        'ENGINES': ['httpx', 'curl'],
        'CRAWL_METHODS': [],
        'LOG_LEVEL': 'DEBUG',
    }

    df = pd.read_csv('t.csv')
    df = df.sample(n=50, random_state=42)  # random_state for reproducibility

    doms = df['dom_tld'].tolist()

    with ISpider(domains=doms, stage="crawl", **config_overrides) as crawler:
        crawler.run()

    with ISpider(domains=doms, stage="spider", **config_overrides) as spider:
        spider.run()