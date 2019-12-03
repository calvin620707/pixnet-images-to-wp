import functools
import mimetypes
import os
import shelve
import uuid
from enum import IntEnum, auto

import requests

import move_images

BASE_DIR = os.path.dirname(os.path.abspath(move_images.__file__))
STORE_DIR = os.path.join(BASE_DIR, 'store')

if not os.path.exists(STORE_DIR):
    os.mkdir(STORE_DIR)


def handle_post_id(f):
    @functools.wraps(f)
    def wrapper(self, post_id: int, *args, **kwargs):
        return f(self, str(post_id), *args, **kwargs)

    return wrapper


class Status(IntEnum):
    TODO = auto()
    DOWNLOADING = auto()
    DOWNLOADED = auto()
    UPLOADING = auto()
    UPLOADED = auto()
    UPDATING = auto()
    DONE = auto()


class StatusStore():
    FILE = f'{STORE_DIR}/posts'

    def __init__(self):
        self.data = shelve.open(self.FILE)

    def __del__(self):
        self.data.close()

    @handle_post_id
    def update(self, post_id: str, status: Status):
        self.data[post_id] = status

    @handle_post_id
    def get(self, post_id: str) -> Status:
        return self.data[post_id]


class ImageStore():
    IMAGE_FOLDER = f'{BASE_DIR}/images'
    INDEX_FILE = f'{STORE_DIR}/index'

    def __init__(self):
        if not os.path.exists(self.IMAGE_FOLDER):
            os.mkdir(self.IMAGE_FOLDER)

        self.index = shelve.open(self.INDEX_FILE)

    def __del__(self):
        self.index.close()

    def _update_url(self, post_id, url, data):
        images = self.index[post_id]
        images.setdefault(url, {})
        images[url].update(data)
        self.index[post_id] = images

    @handle_post_id
    def save_image(self, post_id: str, url: str):
        images = self.index.setdefault(post_id, {})
        if url in images:
            print(f'Skip save_image because URL existed. {url}')
            return

        resp = requests.get(url)
        assert resp.ok, f"{resp} {resp.content}"
        file_ext = mimetypes.guess_extension(resp.headers['content-type'])
        assert file_ext, f"Unknown file type {resp.headers['content-type']}"
        image_file_name = "{}{}".format(uuid.uuid4().hex, file_ext)
        image_path = f'{self.IMAGE_FOLDER}/{image_file_name}'
        if os.path.exists(image_path):
            raise RuntimeError(f"Image ID collision. {image_file_name}")

        with open(image_path, 'wb') as f:
            f.write(resp.content)

        self._update_url(post_id, url, {'file': image_path})

    @handle_post_id
    def get_images(self, post_id: str):
        if post_id in self.index:
            return [(url, data.get('file'), data.get('image_id'))
                    for url, data in self.index[post_id].items()]
        else:
            return []

    @handle_post_id
    def set_wp_image_id(self, post_id: str, url: str, image_id: str):
        self._update_url(post_id, url, {'image_id': image_id})

    @handle_post_id
    def get_wp_image_id(self, post_id: str, url: str):
        return self.index[post_id][url]['image_id']
