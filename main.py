from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build, Resource
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
# SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
SAMPLE_SPREADSHEET_ID = '1E9HaQ0vS6lOrvodZc6_iAqbngfJPupC4zmxidtbSDd8'
# SAMPLE_RANGE_NAME = 'Class Data!A2:E'


def get_credentials():
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            credentials = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return credentials


def main():
    credentials = get_credentials()
    service = build('sheets', 'v4', credentials=credentials)

    sheet: Resource = service.spreadsheets()

    response = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="A1:I").execute()

    table = response['values']
    header = table[0]
    del table[0]

    





if __name__ == '__main__':
    main()
