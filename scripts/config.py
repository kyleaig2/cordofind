import re


COLUMNS = ['Name', 'Handle', 'Playlist URL',
           'Playlist Followers', 'Email', 'Comments', 'Connection']

CSV_DIR = './csvs'

OUT_CSV = CSV_DIR + '/main.csv'

SUBMIT_RE = re.compile(r"(?:send.*|submit.*|email.*)(?:music|song)|(?:music|song)(?:.*submission)", re.I)
BEATS_RE = re.compile(r"(?:send.*|submit.*|email.*)(?:beat|loop)[sz\$]|beat(?:[s\s]*submission)", re.I)

NO_SUBMIT_RE = re.compile(r"(?:don.?t|do not|stop).*(?:send|email).*(?:music|song)", re.I)
NO_BEATS_RE = re.compile(r"(?:don.?t|do not|stop).*(?!send|email).*beats", re.I)
