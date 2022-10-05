import base64
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

client_id = os.environ.get('SPOTIFY_CLIENT_ID')
client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')

def getPlaylistID(url):
    playlistRe = r"spotify\.com/[\/\w]*playlist/([A-Za-z0-9]+)?"
    if results := re.findall(playlistRe, url):
        return results[0]
    else: return None

def getPlaylist(token, url):
    if not (pid := getPlaylistID(url)):
        return None

    url = 'https://api.spotify.com/v1/playlists/' + pid

    headers = {
        'Authorization': 'Bearer ' + token
    }

    r = requests.request('GET', url, headers=headers, data=None)

    data = r.json()

    if r.status_code != 200:
        return None

    # no official spotify playlists
    if data['owner']['id'] == 'spotify':
        return None
    else:
        return data

def getFollowerCount(playlist):
    if 'followers' in playlist:
        return playlist['followers']['total']
    else:
        return -1

def authenticate():
    url = 'https://accounts.spotify.com/api/token'

    payload = 'grant_type=client_credentials'
    auth = base64.b64encode((client_id + ':' + client_secret).encode()).decode()
    headers = {
        'Authorization': 'Basic ' + auth,
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    r = requests.request("POST", url, headers=headers, data=payload)

    return r.json()
