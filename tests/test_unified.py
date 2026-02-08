from ispider_core import ISpider
import pandas as pd

if __name__ == '__main__':
    config_overrides = {
        'USER_FOLDER': '/home/dany/test_scrape_17',
        'POOLS': 32,
        'ASYNC_BLOCK_SIZE': 32,
        'MAXIMUM_RETRIES': 0,
        'CODES_TO_RETRY': [430, 503, 500, 429, -1],
        'CURL_INSECURE': True,
        'MAX_PAGES_POR_DOMAIN': 100000,
        'ENGINES': ['httpx', 'curl'],
        'LOG_LEVEL': 'DEBUG',
        'CRAWL_METHODS': [],
        'TIMEOUT': 30,
        'RESUME': True,
        # SEO modular checks
        'SEO_CHECKS_ENABLED': True,
        'SEO_ENABLED_CHECKS': [],
        'SEO_DISABLED_CHECKS': [],
        'SEO_H1_MAX_CHARS': 70,
        'INCLUDED_EXPRESSIONS_URL': [
            r'^.*/2026/02/08/.*$'
        ],
    }
    doms = ['elmomentoqroo.mx']
    # doms = []
    with ISpider(domains=doms, **config_overrides) as spider:
        spider.run()
    
    

    # df = pd.read_csv('t.csv')
    # doms = df['dom_tld'].tolist()
    
    # df = df.sample(n=10, random_state=42)  # random_state for reproducibility

    # doms = ['1cruisersboulevard.place', '1greatdealauctions.com', '1215design.com', '123nowitsclean.com', '1800waterdamage.com', 
    # 'myshopify.com', 'my1stchoicedetail.com', 'mobiledetailingnampa.com', '1stchoiceweld.com', 'masonryboise.com', 'msha.ke', 
    # 'cyrusramsey.com', 'glossgenius.com', 'martinconstructionboise.com', '208performancetuning.com', '208roofing.com', '208tees.com', 
    # 'myshopify.com', '208taxhelp.com', '21apparel.com', '22northsalon.com', '2csignshop.com', 'apexintegratedsecurity.com', 'https://goagainst.com/', 'gitea.io']

    # doms = ['apexintegratedsecurity.com', 'https://goagainst.com/', 'gitea.io']
    # doms = ['gitea.io']

    # doms = ['deskydoo.com']