import hashlib

def verify_sha256(data: str, expected_hash: str) -> bool:
    """ Verify the SHA-256 hash of the given data. """
    if isinstance(data, bytes):
        data = data.decode()
    if isinstance(data, dict) or isinstance(data, list):
        data = json.dumps(data)
    sha256 = hashlib.sha256()
    sha256.update(data.encode())
    computed_hash = sha256.hexdigest()
    return computed_hash == expected_hash