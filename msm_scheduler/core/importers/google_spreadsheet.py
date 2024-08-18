import os
import pandas as pd
import pdb
import tempfile

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .file import FileImporter
from ..config import Config
from ...constants.gapi import CREDENTIALS_FILE_NAME, SCOPES, TOKEN_FILE_NAME

SHEET_ID = "1B0Yq3AJXZNYVdVV0BpAFWIfRCxL17VsMrnmMxmXePmA"


class GoogleSpreadSheetImporter():

    def __init__(self, sheet_id: str = SHEET_ID):
        self.google_spreadsheet_columns = [
            'Players!A1:F',
            'Player Experiences!A1:F',
            'Player Interests!A1:F',
            'Player Availability!A1:H'
        ]
        self.sheet_id = sheet_id

    @property
    def gapi_credentials(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(TOKEN_FILE_NAME):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE_NAME, SCOPES)
        else:
            creds = None

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE_NAME, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(TOKEN_FILE_NAME, "w") as token:
                token.write(creds.to_json())

        return creds

    def get(self, columns=None):
        config = Config()
        columns = columns or self.google_spreadsheet_columns

        try:
            service = build("sheets", "v4", credentials=self.gapi_credentials)

            # Import data
            sheet = service.spreadsheets()

            if len(columns) == 1:
                return self._get_google_spreadsheet_range(sheet, columns[0])

            data_frames = [self._get_google_spreadsheet_range(sheet, col) for col in columns]
        except HttpError as err:
            print(err)
            return [[], [], [], []]

        df = pd.DataFrame(data_frames[0])
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            config.players_csv_path = tmp.name
            tmp.write(df.to_csv())

        df = pd.merge(df, data_frames[1])
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            config.player_experiences_csv_path = tmp.name
            tmp.write(df.to_csv())

        df = pd.merge(df, data_frames[2])
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            config.player_interests_csv_path = tmp.name
            tmp.write(df.to_csv())

        df = pd.merge(df, data_frames[3])
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            config.player_availabilities_csv_path = tmp.name
            tmp.write(df.to_csv())

        return FileImporter(config).get()

    def _get_google_spreadsheet_range(self, sheet, sheet_range):
        result = sheet.values().get(spreadsheetId=self.sheet_id, range=sheet_range).execute()
        values = result.get("values", [])

        # Add suffix to column names indicating Player Interests (except the 'Name' column)
        if 'Interests' in sheet_range:
            values[0][1:] = [x + '_interest' for x in values[0][1:]]
        return pd.DataFrame(values[1:], columns=values[0])
