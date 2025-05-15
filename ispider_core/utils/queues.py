from collections import deque, Counter

def sparse_q_elements(A):
    """
    Spreads elements from the input list A in a balanced manner
    to minimize consecutive occurrences of the same domain (dom_tld).
    """
    tdict = {}  # Dictionary to store elements grouped by domain
    all_dom_tld = []  # List to store all domain occurrences

    # Group elements by domain and build a list of domains
    for el in A:
        dom_tld = el[2]  # Assuming el[2] contains the domain/tld info
        tdict.setdefault(dom_tld, []).append(el)
        all_dom_tld.append(dom_tld)

    # Spread domain occurrences to create a balanced order
    # print(all_dom_tld)
    spreaded_domains = spread2(all_dom_tld)
    # print(spreaded_domains)
    out = []
    for dom_tld in spreaded_domains:
        if tdict[dom_tld]:  # Ensure there are elements left to pop
            out.append(tdict[dom_tld].pop())

    return out


def spread2(A):
    """
    Distributes elements evenly to prevent clustering of identical values.
    """
    countGroups = {}  # Dictionary mapping counts to lists of values

    # Group values by their frequency
    for value, count in Counter(A).items():
        countGroups.setdefault(count, []).append(value)

    result = []

    # Process counts in ascending order to distribute values evenly
    for count, values in sorted(countGroups.items()):
        result.extend(values)  # Append values to the result list

        if count == 1:
            continue  # No further spreading needed for unique values

        result[:0] = values  # Insert at the beginning for better distribution

        if count == 2:
            continue  # No further processing needed for count=2

        # Calculate chunk size and distribute elements evenly
        chunk, extra = divmod(len(result) - 2 * len(values), count - 1)
        i = 0
        for _ in range(count - 2):
            i += chunk + len(values) + (extra > 0)
            extra -= 1
            result[i:i] = values  # Insert values at calculated positions

    return result


