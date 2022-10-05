import logging
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

    comments = ""
    
    # 1. Has Spotify playlist info
    if playlistUrl:
        match = True
        if playlist := spotify.getPlaylist(token, playlistUrl):
            spFollowTotal = spotify.getFollowerCount(playlist)
        logging.info(realName + "(" + handle + "): " + playlistUrl)
        
    # 2. Accepting submissions? (Or could be explicitly rejecting! lol)
    submitRe = re.compile(r"submi(?:t|ssion*)")
    if submitRe.search(user["description"] + userUrl):
        comments += "Submission "
        match = True

    # 3. Linktree...? see TEEJUS

    # 4. etc...

    if match:
        return [realName, handle, playlistUrl, spFollowTotal, email, comments]
