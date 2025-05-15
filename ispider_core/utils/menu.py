import argparse
import sys

def create_parser():

    # Define a custom formatter to adjust the help layout.
    formatter = lambda prog: argparse.HelpFormatter(prog, max_help_position=52)
    parser = argparse.ArgumentParser(
        description="###### CRAWLER FOR WEBSITES - Multi-Stage Process ######",
        prog='pypoi-ispider',
        formatter_class=formatter
    )

    # Common arguments across stages.
    parser.add_argument('-f', type=str, default="", help="[CRAWL] Input file containing domains")
    parser.add_argument('-o', type=str, default="", help="[CRAWL] Single domain to scrape")
    parser.add_argument('--resume', action='store_true', default=False, help="Resume from previous state, if available")

    # Create subparsers for each stage.
    subparsers = parser.add_subparsers(dest='stage', title='Stages', help='Choose which stage to run')

    # Stage 1: Fetch robots, landing pages, and sitemaps.
    parser_stage1 = subparsers.add_parser('stage1', help='Fetch robots.txt, landing pages, and sitemaps')
    parser_stage1.add_argument('--config', type=str, default="settings.json", help="Configuration file for stage1")

    # Stage 2: Crawl links from Stage 1 (depth 0).
    parser_stage2 = subparsers.add_parser('stage2', help='Crawl links extracted in stage1 (depth 0)')
    parser_stage2.add_argument('--some-option', type=str, help="Additional option for stage2 if needed")

    # Stage 3: Spider links to max_depth.
    parser_stage3 = subparsers.add_parser('stage3', help='Spider all links from stage2 to max depth')
    parser_stage3.add_argument('--max_depth', type=int, default=2, help="Maximum depth to spider")

    # Stage 4: Extract emails, social links, etc.
    parser_stage4 = subparsers.add_parser('stage4', help='Extract emails, social links, etc.')
    parser_stage4.add_argument('--extract_option', type=str, help="Specific extraction options for stage4")

    return parser

def menu():
    parser = create_parser()
    args = parser.parse_args()
    return args
