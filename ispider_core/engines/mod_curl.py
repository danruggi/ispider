import subprocess
import shlex
from datetime import datetime
from ispider_core.utils import domains

def fetch_with_curl(reqA, conf):
    timeout = conf['TIMEOUT']
    url, request_discriminator, dom_tld, retries, depth, engine = reqA
    metadata = {
        'url': url,
        'request_discriminator': request_discriminator,
        'dom_tld': dom_tld,
        'retries': retries,
        'depth': depth,
        'engine': engine,
        'status_code': -1,
        'error_message': None,
        'num_bytes_downloaded': 0,
        'connection_time': datetime.utcnow().isoformat(),
        'content': None
    }

    marker = 'ENDCURLMETADATA'
    sep = '|'  # or whatever separator you use
    write_out = f"\n{marker}{sep}%{{http_code}}{sep}%{{url_effective}}{sep}%{{size_download}}"

    cmd = [
        "curl", "-L", "--max-redirs", "5",
        "--connect-timeout", str(timeout),
        "--silent", "--show-error", "--fail"
    ]

    if conf.get('CURL_INSECURE', False):
        cmd.append("--insecure")

    cmd += ["-w", write_out, url]


    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)

        if result.returncode == 0:
            output = result.stdout
            split_marker = f"\n{marker}{sep}".encode()
            split_index = output.rfind(split_marker)

            if split_index != -1:
                html_part = output[:split_index]  # HTML as bytes
                meta_part = output[split_index + len(split_marker):].decode().strip()

                parts = meta_part.split(sep)
                if len(parts) == 3:
                    metadata['status_code'] = int(parts[0])
                    metadata['num_bytes_downloaded'] = int(parts[2])
                    metadata['content'] = html_part
                    
                    response_url = parts[1]
                    metadata['final_url_raw'] = response_url

                    try:
                        sub, dom, tld, path = domains.get_url_parts(response_url)
                        metadata['final_url_domain_tld'] = dom+"."+tld
                        metadata['final_url_sub_domain_tld'] = sub+"."+dom+"."+tld
                    except Exception as e:
                        metadata['error_message'] = f"Extracting sub/dom/tld: {e}"
                        pass

                    if metadata['final_url_domain_tld'].lower() != metadata['dom_tld'].lower():
                        metadata["status_code"] = -1
                        raise Exception("Redirects not allowed by design")

                else:
                    metadata['error_message'] = f"Unexpected metadata format: {meta_part}"
            else:
                metadata['error_message'] = "Marker not found in curl output"
        else:
            metadata['error_message'] = result.stderr.decode().strip()

    except Exception as e:
        metadata['error_message'] = str(e)

    return metadata
