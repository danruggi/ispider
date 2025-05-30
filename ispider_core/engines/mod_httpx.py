import httpx
import ssl
import warnings

from ispider_core.utils import domains
from ispider_core.parsers import filetype_parser

from datetime import datetime

async def fetch_with_httpx(reqA, client, mod):
    metadata = {}

    # UNPACKING the request
    url, request_discriminator, dom_tld, retries, depth, engine = reqA
    metadata = {
        'url':               url,
        'request_discriminator': request_discriminator,
        'dom_tld':           dom_tld,
        'retries':           retries,
        'depth':             depth,
        'mod':               mod,
        'engine':            engine,
        'status_code':       -1,
        'error_message':     None,
        'num_bytes_downloaded': 0,
        'connection_time':   datetime.utcnow().isoformat(),
    }

    metadata['browser_type'] = 'httpx'
    metadata['browser_version'] = httpx.__version__

    sub, dom, tld, path = domains.get_url_parts(url)
    # metadata['dom_tld'] = dom+"."+tld
    # metadata['dom_tld'] = dom_tld

    try:
        response = await client.get(url=url)
        # Response
        metadata['status_code'] = response.status_code
        metadata['encoding'] = response.encoding
        metadata['reason_phrase'] = response.reason_phrase
        metadata['is_redirect'] = True if response.history else False
        metadata['elapsed'] = str(response.elapsed)
        metadata['num_redirects'] = len(response.history)

        response_url = str(response.url)
        try:
            metadata['final_url_raw'] = response_url;
        except Exception as e:
            pass

        try:
            sub, dom, tld, path = domains.get_url_parts(response_url)
            metadata['final_url_domain_tld'] = dom+"."+tld
            metadata['final_url_sub_domain_tld'] = sub+"."+dom+"."+tld
        except Exception as e:
            pass

        if metadata['final_url_domain_tld'].lower() != metadata['dom_tld'].lower():
            metadata["status_code"] = -1
            raise Exception("Redirects not allowed by design")

        metadata['content'] = response.content

        if filetype_parser.exclude_file_types_from_data(metadata['content']):
            raise Exception("Unsupported file type")

        if metadata['content'] is None:
            raise Exception("Bad content")

        # if conf['WEBSITES_MAX_DEPTH'] > 0 and metadata['depth'] > conf['WEBSITES_MAX_DEPTH']:
        #     raise Exception("Max depth limit")

        try:
            socket = response.stream._stream._httpcore_stream._stream._connection._network_stream.get_extra_info('socket')

            metadata['final_url_resolved'] = socket.getpeername()[0];
            metadata['url_port'] = socket.getpeername()[1];

        except:
            pass

        try:
            ssl_socket = response.stream._stream._httpcore_stream._stream._connection._network_stream.get_extra_info('ssl_object');
            # print(ssl_socket.getpeercert())
            metadata['ssl_common_name'] = ssl_socket.getpeercert()['subject'][0][0][1];
            metadata['ssl_organization_name'] = ssl_socket.getpeercert()['issuer'][1][0][1];
            metadata['ssl_start_date'] = ssl_socket.getpeercert()['notBefore'];
            metadata['ssl_end_date'] = ssl_socket.getpeercert()['notAfter'];
            metadata['ssl_tls_version'] = ssl_socket.version()
        except:
            pass

        try:
            metadata['num_bytes_downloaded'] = response.stream._response.num_bytes_downloaded
        except:
            pass

        try:
            metadata['http_retries'] = int(response.stream._stream._httpcore_stream._stream._connection.info().split(':')[-1].strip())
        except:
            pass

        if response.headers is None:
            raise Exception("No Response Headers")

        # Headers
        metadata['content_length'] = response.headers.get("content-length")
        metadata['content_type'] = response.headers.get("content-type")
        metadata['content_compression'] = response.headers.get("content-encoding")

        try:
            metadata['http_charset'] = response.headers.get('content-type').split(';')[1].split('=')[1] if response.headers.get('content-type') else None
        except:
            pass

        # Added for squarespace
        metadata['server'] = response.headers.get("server")

        metadata['last_modified'] = response.headers.get("last-modified")
        metadata['has_etag'] = bool(response.headers.get("etag"))
        metadata['accept_ranges'] = response.headers.get("accept-ranges")
        metadata['x_powered_by'] = response.headers.get("x-powered-by")
        metadata['server_date'] = response.headers.get('date')

        # Cookies
        metadata['has_cookies'] = bool(response.cookies)
        metadata['cookie_names'] = ";".join(list(response.cookies.keys()))


        # CONNECTION
        metadata['is_dns_error'] = False
        metadata['is_connection_refused'] = False
        metadata['is_timeout'] = False

        # SSL
        metadata['remote_protocol_error'] = False
        metadata['cert_verification_error'] = False
        metadata['is_cert_expired'] = False
        metadata['is_cert_failed'] = False
        metadata['error_message'] = None

        # To be added
        metadata['is_downloaded'] = True;

    except Exception as e:

        ## ADD -5 and -3
        metadata["is_dns_error"] = True if "[Errno -2] Name or service not known" in str(e) or "[Errno -3] Temporary failure in name resolution" in str(e) or " [Errno -5] No address associated with" in str(e) else False
        metadata['is_connection_refused'] = True if "All connection attempts failed" in str(e) else False

        metadata["is_cert_failed"] = isinstance(e, ssl.SSLCertVerificationError)
        metadata["is_cert_expired"] =  isinstance(e, ssl.SSLCertVerificationError) and "certificate has expired" in str(e);

        metadata["is_timeout"] = isinstance(e, httpx.TimeoutException)

        metadata["remote_protocol_error"] = isinstance(e, httpx.RemoteProtocolError)

        metadata['content'] = None
        metadata['is_downloaded'] = False;

        metadata['error_message'] = str(e)

    return metadata