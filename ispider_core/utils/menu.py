# ispider_core/utils/menu.py

import argparse
import sys

try:
    from importlib.metadata import version as get_version
except ImportError:
    from importlib_metadata import version as get_version  # For Python <3.8


def get_package_version():
    try:
        return get_version("ispider")  # Replace with your package name if different
    except Exception:
        return "unknown"


def create_parser():
    version_string = get_package_version()

    parser = argparse.ArgumentParser(
        description="###### CRAWLER FOR WEBSITES - Multi-Stage Process ######",
        prog='ispider',
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=52)
    )

    parser.add_argument('--version', action='version', version=f"%(prog)s {version_string}", help="Show program version and exit")
    parser.add_argument('--resume', action='store_true', help="Resume previous state if available")

    subparsers = parser.add_subparsers(dest='stage', title='Stages', help='Available stages')

    # Crawl subcommand
    parser_crawl = subparsers.add_parser('crawl', help='Crawl stage: fetch landings, robots, sitemaps')
    parser_crawl.add_argument('-f', type=str, help="Input CSV file with domains (column name: dom_tld)")
    parser_crawl.add_argument('-o', type=str, help="Single domain to scrape")

    # Spider subcommand
    parser_spider = subparsers.add_parser('spider', help='Spider stage: follow links to max depth')
    parser_spider.add_argument('-f', type=str, help="Input CSV file with domains (column name: dom_tld)")
    parser_spider.add_argument('-o', type=str, help="Single domain to scrape")

    # Unified subcommand
    parser_unified = subparsers.add_parser('unified', help='Spider stage: follow links to max depth')
    parser_unified.add_argument('-f', type=str, help="Input CSV file with domains (column name: dom_tld)")
    parser_unified.add_argument('-o', type=str, help="Single domain to scrape")

    # API subcommand
    parser_api = subparsers.add_parser('api', help='API server')
    parser_api.add_argument('--ui-pid', type=int, help="PID of the macOS UI process")

    return parser

    
def menu():
    parser = create_parser()
    args = parser.parse_args()
    return args
