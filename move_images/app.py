from move_images.tasks import get_posts, update_post

posts = get_posts()

for p in posts:
    update_post(p)
