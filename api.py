from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = # one or more scopes (strings)
CLIENT_SECRET = 'client_secret.json'

store = file.Storage('storage.json')
credz = store.get()
if not credz or credz.invalid:
    flow = client.flow_from_clientsecrets(CLIENT_SECRET, SCOPES)
    credz = tools.run(flow, store)
    
SERVICE = build(API, VERSION, http=credz.authorize(Http()))