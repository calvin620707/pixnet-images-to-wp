import functools
import os

import requests.auth
import requests_toolbelt.sessions
from tqdm import tqdm

from .util import find_pixnet_image_urls, post

client = requests_toolbelt.sessions.BaseUrlSession(
    f"{os.environ['WP_URL'].strip('/')}/wp-json/wp/v2/")
client.auth = requests.auth.HTTPBasicAuth(os.environ['WP_USER'],
                                          os.environ['WP_PASSWORD'])

post_store = post.StatusStore()
image_store = post.ImageStore()

PAGE_SIZE = 50


def get_posts():
    posts = []
    has_next = True
    page = 1
    print("Start getting posts...")
    while has_next:
        new = client.get('posts', params={
            'page': page,
            'per_page': PAGE_SIZE
        }).json()
        posts.extend(new)
        print(f"Got {len(new):2d} posts in page {page:2d}.")
        has_next = len(new) == PAGE_SIZE
        page += 1

    for p in posts:
        p['title'] = p['title']['rendered']

    print(f"Total post: {len(posts)}")
    return posts


def update_post(post_obj: dict):
    print(f"Start updating {post_obj['title']}")
    _download_images(post_obj)
    _upload_images(post_obj)
    _update_post_links(post_obj)


def _task(current_status):
    def dec(fn):
        @functools.wraps(fn)
        def wrap(post_obj: dict, *args, **kwargs):
            try:
                p_status = post_store.get(post_obj['id'])
                if p_status >= current_status:
                    msg = ("Skip. Post status is {} and current status is {}."
                           " {}.".format(str(p_status), str(current_status),
                                         post_obj['title']))
                    print(msg)
                    return
            except KeyError:
                print(f"Not status for {post_obj['title']}")
                post_store.update(post_obj['id'], post.Status.TODO)
                pass

            print("{} starts for {}".format(str(current_status),
                                            post_obj['title']))

            ret = fn(post_obj, *args, **kwargs)

            post_store.update(post_obj['id'], post.Status(current_status + 1))
            print("{} finished for {}".format(str(current_status),
                                              post_obj['title']))
            return ret

        return wrap

    return dec


@_task(post.Status.DOWNLOADING)
def _download_images(post_obj: dict):
    urls = find_pixnet_image_urls(post_obj['content']['rendered'])
    for u in tqdm(list(urls), desc="Downloading"):
        image_store.save_image(post_obj['id'], u)


@_task(post.Status.UPLOADING)
def _upload_images(post_obj: dict):
    images = tqdm(image_store.get_images(post_obj['id']), desc="Uploading")
    for url, file_path, image_id in images:
        with open(file_path, 'rb') as f:
            resp = client.post('media', files={'file': f})
        assert resp.ok, f"Upload image failed. {resp} {resp.content}."
        image_store.set_wp_image_id(post_obj['id'], url, resp.json()['id'])


@_task(post.Status.UPDATING)
def _update_post_links(post_obj: dict):
    resp = client.get(f"posts/{post_obj['id']}")
    content = resp.json()['content']['rendered']
    images = image_store.get_images(post_obj['id'])
    if not images:
        print("Skip. No need to update.")
        return

    images = tqdm(images, desc="Updateing")
    for url, _, image_id in images:
        wp_image_url = client.get(f"media/{image_id}").json()['link']
        content = content.replace(url, wp_image_url)
    resp = client.post(f"posts/{post_obj['id']}", json={'content': content})
    assert resp.ok, "Failed to update {} {} {}.".format(
        post_obj['title'], resp, resp.content)
