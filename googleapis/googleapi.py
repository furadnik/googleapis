from __future__ import print_function
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/books', 'https://www.googleapis.com/auth/tasks', 'https://mail.google.com/', 'https://www.googleapis.com/auth/youtube', 'https://www.googleapis.com/auth/calendar']

def get_service(b, v="v3", get_creds=False, user=""):
    token_path = os.path.join(os.path.expanduser("~"),'.config', 'tmq', 'googleapis', 'creds', user + 'token.pickle')
    creds_path = os.path.join(os.path.expanduser("~"),'.config', 'tmq', 'googleapis', 'creds', user + 'creds_new.json')

    if not os.path.exists(creds_path):
        return None

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    if get_creds:return creds
    service = build(b, v, credentials=creds)
    return service

