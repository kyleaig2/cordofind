import logging
from scripts.config import BEATS_RE, NO_BEATS_RE, NO_SUBMIT_RE, SUBMIT_RE
from scripts import spotify
import re

def getUserUrl(user):
    url = ''
    if user['url']:
        if 'expanded_url' in user['entities']['url']['urls'][0]:
            url = user['entities']['url']['urls'][0]['expanded_url']
    return url

def getPlaylistUrl(user):
    playlistUrl = None
    if url := getUserUrl(user):
        if 'playlist' in url:
            playlistUrl = url
    return playlistUrl

def getEmailAddress(user):
    emailRe = r"[\w.]+@[\w.]+[\w]+"
    if results := re.findall(emailRe, user["description"]):
        return results[0]
    else: return None

def createMatch(user, token):
    match = False

    realName = user["name"]
    handle = user["username"]
    userUrl = getUserUrl(user)
    playlistUrl = getPlaylistUrl(user)
    spFollowTotal = 0
    email = getEmailAddress(user)

    comments = []
    
    # 1. Has Spotify playlist info
    if playlistUrl:
        match = True
        if playlist := spotify.getPlaylist(token, playlistUrl):
            spFollowTotal = spotify.getFollowerCount(playlist)
        logging.info(realName + "(" + handle + "): " + playlistUrl)
        
    # 2. Accepting submissions?
    if SUBMIT_RE.search(user["description"] + userUrl) and not NO_SUBMIT_RE.search(user["description"]):
        comments += ["Submission"]
        match = True

    # 3. Accepting beats
    if BEATS_RE.search(user["description"] + userUrl) and not NO_BEATS_RE.search(user["description"]):
        comments += ["Beat Submission"]
        match = True
        logging.info("Beat Submission: " + realName + "(" + handle + ")")

    # 4. Linktree...? see TEEJUS

    # 5. etc...

    if match:
        return [realName, handle, playlistUrl, spFollowTotal, email, ','.join(comments)]
