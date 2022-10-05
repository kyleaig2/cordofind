import csv
import math
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging
import sys
import os
from scripts import apple
from scripts import spotify
from scripts import utils
from json.decoder import JSONDecodeError
from dotenv import load_dotenv

"""
    Hello. Welcome to the source code for my program.
    TODO: Run this program on large Twitter accounts when not editing
    TODO: Test campaign on Kyle Corduroy Love Us, record results
    TODO: Using results from test campaign, do another test with Belladonna, record results
"""

load_dotenv()

# Twitter HTTP Session
sesh = requests.Session()
bearer = os.environ.get('TWITTER_BEARER_TOKEN')

# Spotify HTTP
authJSON = {}
expireAt = 0

# Log file setup
logging.basicConfig(filename="./app.log", format="%(asctime)s [%(levelname)s]: %(message)s", level=logging.INFO)
csvDir = './csvs'

def check():
    if not bearer:
        raise Exception('Missing TWITTER_BEARER_TOKEN')

def init():
    global sesh
    adapter = HTTPAdapter(max_retries=Retry(total=10, backoff_factor=60))
    sesh.headers.update({'Authorization' : 'Bearer ' + bearer})
    sesh.mount('https://api.twitter.com/2/users', adapter)
    
    try:
        reauthenticate()
    except:
        logging.error("Error establishing HTTP Connection with Spotify")

def getAuthJSON():
    global authJSON
    return authJSON

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
    check()
    init()

    # Loop through console arguments (target twitter accounts)
    args = sys.argv[1:]
    idJSONs = getTwitterIDJSONs(args)
    try:
        idJSONs = getTwitterIDJSONs(args)
    except Exception as e:
        logging.error("Error establishing HTTP Connection with Twitter")
        raise e
    
    for idJSON in idJSONs:
        target = idJSON['username'].lower()
        tid = idJSON['id']
        logging.info("starting: " + target)
        numAcctsSearched = 0
        initCSV(target)
        pageToken =  ""
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
                # Has token expired?
                if (time.time() >= expireAt) or 'access_token' not in authJSON:
                    reauthenticate()

                # Write to CSV
                if match := utils.createMatch(user, authJSON['access_token']):
                    writeToCSV([*match, target], target)

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
    try:
        main()
    except Exception as e:
        logging.error(e)
        apple.notify('CordoFind', 'An error occurred')
