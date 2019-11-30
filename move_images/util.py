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
    DOWNLOADED = 2
    UPLOADED = 3
    DONE = 4

    def to_str(self, status) -> str:
        return {
            self.TODO: 'Todo',
            self.DOWNLOADED: 'Downloaded',
            self.UPLOADED: 'Uploaded',
            self.DONE: 'Done',
        }[status]


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
    IMAGE_FOLDER = '{}/images'.format(os.path.dirname(os.path.abspath(__file__)))
    INDEX_FILE = f'{IMAGE_FOLDER}/index.json'

    def __init__(self):
        if not os.path.exists(self.IMAGE_FOLDER):
            os.mkdir(self.IMAGE_FOLDER)

        self.index = collections.defaultdict(list)
        if os.path.exists(self.INDEX_FILE):
            self.index.update(json.load(open(self.INDEX_FILE, 'r')))

    def _update_index(self, post_id: str, url: str, data: dict):
        self.index[post_id][url].update(data)
        json.dump(self.index, open(self.INDEX_FILE, 'w'))

    def save_image(self, post_id: str, url: str):
        images = self.index[post_id]
        if url in images:
            print(f'Skip save_image because URL existed. {url}')
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

        self._update_index(post_id, url, {'file': image_path})

    def get_images(self, post_id: str):
        return [(url, data['file'], data.get('image_id'))
                for url, data in self.index[post_id].items()]

    def set_wp_image_id(self, post_id: str, url: str, image_id: str):
        self._update_index(post_id, url, {'image_id': image_id})

    def get_wp_image_id(self, post_id: str, url: str):
        ret = self.index[post_id][url].get('image_id')
        if not ret:
            raise KeyError

        return ret
