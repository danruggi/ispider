import os
import json
import pathlib
import hashlib
from collections import defaultdict

from ispider_core.utils import ifiles
from ispider_core.utils import domains

from bs4 import BeautifulSoup

def load_website_content(conf, urls, output_path):
    """
    Combine all HTML content associated with URLs for a given dom_tld into a single JSON file.
    """

    website_data_by_domain = {}

    doms = []
    for url in urls:
        sub, dom, tld, path = domains.get_url_parts(url)
        dom_tld = f"{dom}.{tld}"
        doms.append(dom_tld)

    json_paths = pathlib.Path(conf['path_jsons']).rglob("*.json")

    for json_path in json_paths:
        print(f"Scanning JSONs in: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                url = entry.get("url")
                rd = entry.get("request_discriminator")
                dom_tld = entry.get("dom_tld")
                status_code = entry.get("status_code")


                if dom_tld not in doms:
                    continue
                
                if dom_tld not in website_data_by_domain:
                    website_data_by_domain[dom_tld] = {"pages": {}}

                if status_code != 200:
                    continue

                if rd == 'landing_page':
                    html_path = "njfuture.org/_.html"
                else:
                    html_path = entry.get("fname", None)

                if not html_path:
                    continue

                print(html_path)
                html_path = os.path.join(conf['path_dumps'], html_path)

                try:
                    html_content = pathlib.Path(html_path).read_text(encoding='utf-8', errors='ignore')
                    soup = BeautifulSoup(html_content, "html.parser")
                    main_content_div = soup.find("div", id="njf-main-content")
                    main_content = main_content_div.decode_contents() if main_content_div else ""
                    page_title = soup.title.string.strip() if soup.title and soup.title.string else ""

                except Exception as e:
                    print(f"Error reading or parsing {html_path}: {e}")
                    continue

                # Save the data
                website_data_by_domain[dom_tld]["pages"][url] = {
                    "status_code": entry.get("status_code"),
                    "html": html_content,
                    "page_title": page_title,
                    "main_content": main_content,
                    # "page_file": html_path,
                }

                # html_path = ifiles.get_dump_file_name(rd, url, dom_tld, conf)

                if not os.path.isfile(html_path):
                    print(f"{entry.get("status_code")}")
                    print(f"Missing HTML file: {html_path}")
                    continue

                try:
                    html_content = pathlib.Path(html_path).read_text(encoding='utf-8', errors='ignore')
                except Exception as e:
                    print(f"Error reading {html_path}: {e}")
                    continue


     # Write output
    for dom_tld, data in website_data_by_domain.items():
        output_file = pathlib.Path(output_path) / f"{dom_tld}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as out_f:
            json.dump(data, out_f, indent=2, ensure_ascii=False)
        print(f"Saved {output_file}")