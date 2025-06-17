
import os
import csv
import sys
from ispider_core.utils.menu import menu
from ispider_core.ispider import ISpider
import subprocess

from ispider_core.api_server import app, Server, close_spider

def main():
    args = menu()

    if args.stage is None:
        print("No valid stage selected. Use -h for help.")
        sys.exit(1)

    if args.stage == 'api':

        print("🚀 Starting API server...")
        import uvicorn

        if args.ui_pid:
            print(f"[iSpider] 💻 UI PID received: {args.ui_pid}")
            os.environ["ISP_UI_PID"] = str(args.ui_pid)

        config = uvicorn.Config(app, host="0.0.0.0", port=8000, access_log=False)
        server = Server(config)
        server.run_and_wait()

        return
        
    if not args.f and not args.o:
        print("Please provide either -f <file.csv> or -o <domain>")
        sys.exit(1)

    domains = []
    if args.f:
        try:
            with open(args.f, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                if 'dom_tld' not in reader.fieldnames:
                    print("Column 'dom_tld' not found in file.")
                    sys.exit(1)

                # Read all values of 'dom_tld' column, ignoring empty strings
                domains = list({row['dom_tld'] for row in reader if row['dom_tld'].strip()})
        except Exception as e:
            print(f"Error reading file {args.f}: {e}")
            sys.exit(1)

    elif args.o:
        domains = [args.o]

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

    spider = ISpider(domains=domains, stage=args.stage, **config_overrides)
    spider.run()

if __name__ == "__main__":
    main()
