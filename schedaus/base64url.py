import base64


def decode_base64url(s):
    return base64.urlsafe_b64decode(s + '=' * ((4 - len(s) & 3) & 3)).decode()
