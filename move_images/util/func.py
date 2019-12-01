import re

URL_RE_PTN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+' # noqa
)


def find_urls(string):
    return URL_RE_PTN.findall(string)


def find_pixnet_image_urls(post_content: str) -> list:
    return filter(lambda u: 'pic.pimg.tw' in u, find_urls(post_content))
