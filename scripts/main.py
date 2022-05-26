import csv
import math
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import re
import time
import logging
import sys
import os
import spotify
import apple
from json.decoder import JSONDecodeError

"""
    Hello. Welcome to the source code for my program.
    TODO: Run this program on large Twitter accounts when not editing
    TODO: Test campaign on Kyle Corduroy Love Us, record results
    TODO: Using results from test campaign, do another test with Belladonna, record results
"""

# Twitter HTTP Session
sesh = requests.Session()
bearer = os.environ.get('TWITTER_BEARER_TOKEN')

# Spotify HTTP
authJSON = {}
expireAt = 0

# Log file setup
logging.basicConfig(filename="../app.log", format="%(asctime)s [%(levelname)s]: %(message)s", level=logging.INFO)
csvDir = '../csvs'

def init():
    global sesh
    adapter = HTTPAdapter(max_retries=Retry(total=10, backoff_factor=60))
    sesh.headers.update({'Authorization' : 'Bearer ' + bearer})
    sesh.mount('https://api.twitter.com/2/users', adapter)
    
    try:
        reauthenticate()
    except:
        logging.error("Error establishing HTTP Connection with Spotify")


def getTwitterIDJSONs(handles):
    jsons = []
    r = sesh.get('https://api.twitter.com/2/users/by?usernames='+','.join(handles))
    if 'data' in r.json():
        userList = r.json()['data']
        for user in userList:
            jsons.append(user)
    if 'errors' in r.json():
        for error in r.json()['errors']:
            if 'detail' in error:
                logging.error(error['detail'])
            elif 'message' in error:
                logging.error(error['message'])
    return jsons

def getTwitterFollowersJSON(tid, pageToken):
    global sesh
    data = {}
    parameters = 'user.fields=description,url,entities&max_results=1000'+pageToken
    r = sesh.get('https://api.twitter.com/2/users/'+str(tid)+'/followers?'+parameters)

    if r.status_code == 429 or 'data' not in r.json():
        try:
            sleep = int(r.headers['x-rate-limit-reset']) - time.time()
        except:
            sleep = 900
        logging.info("sleeping for " + str(math.ceil(sleep/60)) + " min")
        time.sleep(sleep)
        logging.info("resuming")
        r = sesh.get('https://api.twitter.com/2/users/'+str(tid)+'/followers?'+parameters)

    elif r.status_code == 400:
        logging.error('code 400')
        logging.error(r.headers)
        logging.error(str(r.status_code) + ': ' + r.text)

    try:
        data = r.json()
    except JSONDecodeError:
        logging.error("Error parsing response:")
        logging.error(r.headers)
        logging.error(r.text)
    except Exception as e:
        logging.error(e)
        logging.error("An unknown exception occurred")
        logging.error(r.headers)
        logging.error(r.text)
        
    return data

def getEmailAddress(user):
    emailRe = r"[\w.]+@[\w.]+[\w]+"
    if results := re.findall(emailRe, user["description"]):
        return results[0]
    else: return None

def getPlaylistUrl(user):
    playlistUrl = None
    if url := getUserUrl(user):
        if 'playlist' in url:
            playlistUrl = url
    return playlistUrl

def getUserUrl(user):
    url = ''
    if user['url']:
        if 'expanded_url' in user['entities']['url']['urls'][0]:
            url = user['entities']['url']['urls'][0]['expanded_url']
    return url

def getSpFollowTotal(pid):
    if (time.time() >= expireAt) or 'access_token' not in authJSON: # Has token expired?
        reauthenticate()
    return spotify.getFollowerCount(authJSON["access_token"], pid)

def reauthenticate():
    global authJSON, expireAt
    authJSON = spotify.authenticate()
    expireAt = time.time() + authJSON["expires_in"]

def initCSV(name):
    os.makedirs(csvDir+'/'+name, exist_ok=True)
    with open(csvDir+'/'+name+'/'+name+'_followers.csv', mode='w') as twitterFile:
        tweeter = csv.writer(twitterFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        tweeter.writerow(["Name", "Handle", "Playlist URL", "Playlist Followers", "Email", "Comments", "Connection"])

def writeToCSV(row, name):
    with open(csvDir+'/'+name+'/'+name+'_followers.csv', mode='a') as twitterFile:
        tweeter = csv.writer(twitterFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        tweeter.writerow(row)

def main():
    init()

    # Loop through console arguments (target twitter accounts)
    args = sys.argv[1:]
    idJSONs = getTwitterIDJSONs(args)
    try:
        idJSONs = getTwitterIDJSONs(args)
    except Exception as e:
        logging.error("Error establishing HTTP Connection with Twitter")
        logging.error(e)
        quit()
    
    for idJSON in idJSONs:
        target = idJSON['username'].lower()
        tid = idJSON['id']
        logging.info("starting: " + target)
        numAcctsSearched = 0
        initCSV(target)
        pageToken = '&pagination_token=CM9GLAHL5K81CZZZ'
        # Pagination Loop
        while True:
            # Retrieve User JSON List
            if not (fJSON := getTwitterFollowersJSON(tid, pageToken)):
                logging.error("Couldn't get the next page of " + target + "'s followers")
                break
            userList = fJSON['data']
            meta = fJSON['meta']
            
            # Data search`
            for user in userList:
                realName = user["name"]
                handle = user["username"]
                userUrl = getUserUrl(user)
                playlistUrl = getPlaylistUrl(user)
                spFollowTotal = 0
                email = getEmailAddress(user)
                comments = ""
                match = False

                if playlistUrl:
                    match = True
                    if pid := spotify.getPlaylistID(playlistUrl):
                        spFollowTotal = getSpFollowTotal(pid)
                    logging.info(realName + "(" + handle + "): " + playlistUrl)
                    
                # Accepting submissions? (Or could be explicitly rejecting! lol)
                submitRe = re.compile(r"submi(?:t|ssion*)")
                if submitRe.search(user["description"] + userUrl):
                    comments += "Submission "
                    match = True

                # Write to CSV
                if match:
                    writeToCSV([realName, handle, playlistUrl, spFollowTotal, email, comments, target], target)

                # Increment accounts searched count
                numAcctsSearched+=1
                
            # end for
            # Next page or break
            if 'next_token' in meta:
                nextToken = meta["next_token"]
                pageToken = '&pagination_token='+nextToken
            else:
                break
        # end while
        logging.info(target + " finished. " + str(numAcctsSearched) + " accounts searched")
        apple.notify('CordoFind', 'Finished ' + target)
    # end for

if __name__ == '__main__':
    #main()
    try:
        main()
    except Exception as e:
        logging.error(e)
        apple.notify('CordoFind', 'An error occurred')
