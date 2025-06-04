# ispider_core/__main__.py

import sys
import pandas as pd
from ispider_core.utils.menu import menu
from ispider_core.utils.logger import LoggerFactory
from ispider_core.ispider import ISpider  # Make sure this is the actual class location

def main():
    args = menu()

    if args.stage is None:
        print("❌ No valid stage selected. Use -h for help.")
        sys.exit(1)

    if not args.f and not args.o:
        print("❌ Please provide either -f <file.csv> or -o <domain>")
        sys.exit(1)

    # Get domain list
    domains = []
    if args.f:
        try:
            df = pd.read_csv(args.f)
            if 'dom_tld' not in df.columns:
                print("❌ Column 'dom_tld' not found in file.")
                sys.exit(1)
            domains = df['dom_tld'].dropna().unique().tolist()
        except Exception as e:
            print(f"❌ Error reading file {args.f}: {e}")
            sys.exit(1)

    elif args.o:
        domains = [args.o]

    # Minimal configuration (extend if needed)
    config_overrides = {
        'USER_FOLDER': '~/.ispider/',
        'POOLS': 4,
        'ASYNC_BLOCK_SIZE': 4,
        'MAXIMUM_RETRIES': 2,
        'CODES_TO_RETRY': [430, 503, 500, 429],
        'CURL_INSECURE': True,
        'ENGINES': ['httpx', 'curl'],
        'CRAWL_METHODS': ['robots', 'sitemaps'],
        'LOG_LEVEL': 'INFO',
    }

    # print(f"🚀 Running stage: {args.stage} on {len(domains)} domain(s)")
    spider = ISpider(domains=domains, stage=args.stage, **config_overrides)
    spider.run()

if __name__ == "__main__":
    main()
