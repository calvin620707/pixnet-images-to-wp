from move_images.tasks import client, update_post

# posts = get_posts()

# for p in posts[:1]:
#     update_post(p)

post = client.get('posts', params={'search': '香港觀光懶人包'}).json()
post = post[0]
post['title'] = post['title']['rendered']
update_post(post)
