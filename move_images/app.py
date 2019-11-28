import os

import requests.auth
import requests_toolbelt.sessions

from .util import *

client = requests_toolbelt.sessions.BaseUrlSession(
    f"{os.environ['WP_URL'].strip('/')}/wp-json/wp/v2/")
client.auth = requests.auth.HTTPBasicAuth(os.environ['WP_USER'],
                                          os.environ['WP_PASSWORD'])

posts = client.get('posts').json()