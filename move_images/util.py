import uuid
import mimetypes
import collections
import requests
import json
import os
import re

URL_RE_PTN = re.compile(
    u'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)


def find_urls(string):
    return URL_RE_PTN.findall(string)


def find_pixnet_image_urls(post_content: str) -> list:
    return find_urls(post_content)


class PostStatus():
    TODO = 1
    DONE = 2


class PostStatusStore():
    FILE = './posts.json'

    def __init__(self):
        self.data = collections.defaultdict(lambda: PostStatus.TODO)
        if os.path.exists(self.FILE):
            f = open(self.FILE, 'r')
            self.data.update(json.load(f))

    def update(self, post_id: str, status: PostStatus):
        self.data[post_id] = status
        f = open(self.FILE, 'w')
        json.dump(self.data, f)

    def get_status(self, post_id: str) -> PostStatus:
        if post_id not in self.data:
            raise KeyError()

        return self.data.get(post_id)


class PostImageStore():
    IMAGE_FOLDER = './images'
    INDEX_FILE = f'{IMAGE_FOLDER}/index.json'

    def __init__(self):
        if not os.path.exists(self.IMAGE_FOLDER):
            os.mkdir(self.IMAGE_FOLDER)

    def save_image(self, post_id: str, url: str):
        index = collections.defaultdict(list)
        if os.path.exists(self.INDEX_FILE):
            index.update(json.load(open(self.INDEX_FILE, 'r')))

        images = index[post_id]
        if url in [i['url'] for i in images]:
            print(f'URL existed. {url}')
            return

        resp = requests.get(url)
        image_file_name = "{}{}".format(
            uuid.uuid4().hex,
            mimetypes.guess_extension(resp.headers['content-type']))
        image_path = f'{self.IMAGE_FOLDER}/{image_file_name}'
        if os.path.exists(image_path):
            raise RuntimeError(f"Image ID collision. {image_file_name}")

        with open(image_path, 'wb') as f:
            f.write(resp.content)

        index[post_id].append({'url': url, 'file': image_path})
        json.dump(index, open(self.INDEX_FILE, 'w'))
