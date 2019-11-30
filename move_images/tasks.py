import os
import functools

import requests.auth
import requests_toolbelt.sessions

from .util import (PostImageStore, PostStatus, PostStatusStore,
                   find_pixnet_image_urls)

client = requests_toolbelt.sessions.BaseUrlSession(
    f"{os.environ['WP_URL'].strip('/')}/wp-json/wp/v2/")
client.auth = requests.auth.HTTPBasicAuth(os.environ['WP_USER'],
                                          os.environ['WP_PASSWORD'])

post_store = PostStatusStore()
image_store = PostImageStore()

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

    print(f"Total post: {len(posts)}")
    return posts


def update_post(post: dict):
    print(f"Start updating {post['title']}")
    _download_images(post)
    _upload_images(post)
    _update_post_links(post)


def check_status(current_status):
    def dec(fn):
        @functools.wraps
        def wrap(post: dict, *args, **kwargs):
            p_status = post_store.get_status(post['id'])
            if p_status >= current_status:
                print("Skip. {} is {} and current status is {}.".format(
                    post['title'], PostStatus.to_str(p_status),
                    PostStatus.to_str(current_status)))
                return

            print("{} starts for {}".format(PostStatus.to_str(current_status),
                                            post['title']))

            ret = fn(post, *args, **kwargs)

            post_store.update(post['id'], current_status)
            print("{} finished for {}".format(
                PostStatus.to_str(current_status), post['title']))
            return ret

        return wrap

    return dec


@check_status(PostStatus.DOWNLOADED)
def _download_images(post: dict):
    urls = find_pixnet_image_urls(post['content']['rendered'])
    post_store.update(post['id'], PostStatus.TODO)
    for u in urls:
        print(f"Downloading {u}...")
        image_store.save_image(post['id'], u)


@check_status(PostStatus.UPLOADED)
def _upload_images(post: dict):
    for url, file_path, image_id in image_store.get_images(post['id']):
        file_name = os.path.basename(file_path)
        print(f"Uploading {file_name}...")
        resp = client.post('media', files={file_name: open(file_path, 'rb')})
        assert resp.ok, f"Upload image failed. {resp} {resp.content}."
        image_store.set_wp_image_id(post['id'], url, resp.json()['id'])


@check_status(PostStatus.DONE)
def _update_post_links(post: dict):
    content = client.get(f"posts/{post['id']}").json()['content']['rendered']
    for url, _, image_id in image_store.get_images(post['id']):
        wp_image_url = client.get(f"media/{image_id}").json()['source_url']
        content = content.replace(url, wp_image_url)
    resp = client.post(f"posts/{post['id']}", json={'content': content})
    assert resp.ok, f"Failed to update {post['title']} {resp} {resp.content}."
