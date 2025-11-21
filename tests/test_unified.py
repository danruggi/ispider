from ispider_core import ISpider
import pandas as pd

if __name__ == '__main__':
    config_overrides = {
        'USER_FOLDER': '/Volumes/Sandisk2TB/test_business_scraper_29',
        'POOLS': 32,
        'ASYNC_BLOCK_SIZE': 32,
        'MAXIMUM_RETRIES': 2,
        'CODES_TO_RETRY': [430, 503, 500, 429, -1],
        'CURL_INSECURE': True,
        'MAX_PAGES_POR_DOMAIN': 100000,
        'ENGINES': ['httpx', 'curl'],
        'LOG_LEVEL': 'DEBUG',
        'CRAWL_METHODS': [],
    }

    df = pd.read_csv('t.csv')
    doms = df['dom_tld'].tolist()
    
    # df = df.sample(n=10, random_state=42)  # random_state for reproducibility


    doms = ['1cruisersboulevard.place', '1greatdealauctions.com', '1215design.com', '123nowitsclean.com', '1800waterdamage.com', 
    'myshopify.com', 'my1stchoicedetail.com', 'mobiledetailingnampa.com', '1stchoiceweld.com', 'masonryboise.com', 'msha.ke', 
    'cyrusramsey.com', 'glossgenius.com', 'martinconstructionboise.com', '208performancetuning.com', '208roofing.com', '208tees.com', 
    'myshopify.com', '208taxhelp.com', '21apparel.com', '22northsalon.com', '2csignshop.com']

    # doms = ['deskydoo.com']
    # doms = ['1800waterdamage.com']
    # doms = []
    with ISpider(domains=doms, stage="unified", **config_overrides) as spider:
        spider.run()
    
    