# http_retry.py

import time
from ispider_core.utils import engine


def should_retry(resp, conf, logger, qout, mod):
    """
    Handle retry logic for HTTP responses.

    Returns:
        True if the response was queued for retry, False otherwise.
    """
    status_code = resp['status_code']
    url = resp['url']
    rd = resp['request_discriminator']
    dom_tld = resp['dom_tld']
    retries = resp['retries']
    depth = resp['depth']
    current_engine = resp['engine']
    error_message = resp['error_message']

    # Retry on specific HTTP status codes
    if status_code in conf['CODES_TO_RETRY'] and retries < conf['MAXIMUM_RETRIES']:
        next_engine = engine.EngineSelector(conf['ENGINES']).next_cyclic(current_engine)
        logger.debug(
            f"[{mod}] [{status_code}] -- D:{depth} -- R:{retries} -- E:{current_engine} -> {next_engine} -- RETRY [{error_message}] [{dom_tld}] {url}"
        )
        time.sleep(conf['TIME_DELAY_RETRY'])
        qout.put((url, rd, dom_tld, retries + 1, depth, next_engine))
        return True

    # Retry on specific error messages
    if resp.get('error_message') is not None:
        if '[Errno 0] Error' in resp['error_message'] and retries <= conf['MAXIMUM_RETRIES']:
            logger.debug(f"[Errno 0] -- RETRY E:{current_engine}: {url}, {retries}, {depth}")
            qout.put((url, rd, dom_tld, retries + 1, depth, current_engine))
            return True

    return False
