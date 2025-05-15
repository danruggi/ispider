def exclude_file_types_from_data(data):
    ## JPG
    if data[:2] == b'\xFF\xD8':
        return True

    # PNG
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return True

    # PDF
    if data[:5] == b'%PDF-':
        return True

    # WEBP/RIFF
    if data[:4] == b'RIFF':
        return True

    # ICS
    if data[:4] == b'BEGIN:V':
        return True

    # OGV
    if data[:4] == b'\x4F\x67\x67\x53':
        return True

    # MPG
    if data[:4] == b'\x00\x00\x01\xBA':
        return True

    # MP4, MOV, M4V
    if data[:4] == b'\x00\x00\x00\x14' or data[:4] == b'\x66\x74\x79\x70':
        return True

    # ZIP
    if data[:4] == b'PK\x03\x04':
        return True

    # RAR
    if data[:7] == b'\x52\x61\x72\x21\x1A\x07\x00':
        return True

    return False
