import os, sys
import json

from ispider_core import ISpider

from ispider_core.addons import out_parser_full_to_json as pj

if __name__ == '__main__':

    # List of websites
    urls = ["https://www.example_1.org/", "https://www.example_2.org/"]

    # A
    ispider = ISpider(domains=urls)

    # Get just the homepages    
    ispider.stage = "stage1"
    ispider.run()

    # Spider all pages
    ispider.stage = "stage2"
    ispider.run()

    # Actual conf
    print(ispider.conf)

    # Example parser to export all website contents in jsons
    output_path = 'tests/outs'
    os.makedirs(output_path, exist_ok=True)
    
    pj.load_website_content(ispider.conf, urls, output_path)