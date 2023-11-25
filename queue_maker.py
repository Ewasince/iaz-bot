import itertools
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from errors import EmptyList

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample sp
#
# readsheet.
SAMPLE_RANGE_NAME = "A2:E2"

StudentAndTheme = tuple[str, str, str]


class SheetWrapper:

    def __init__(self, sheet_id: str, use_titles=True):
        self.sheet_id = sheet_id
        self.start_row = 2 if use_titles else 1
        """Shows basic usage of the Sheets API.
           Prints values from a sample spreadsheet.
           """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        service = build("sheets", "v4", credentials=creds)

        self.sheet = service.spreadsheets()
        pass

    def get_sheet_lists(self) -> list[str]:
        """
        0 – first main list
        :return:
        """

        spreadsheet = self.sheet.get(spreadsheetId=self.sheet_id).execute()
        sheet_list = spreadsheet.get('sheets')
        sheet_list = [s['properties']['title'] for s in sheet_list]
        # sheet_dict = {s['properties']['title'] : n for n, s in enumerate(sheet_list)}
        # for sheet in sheet_list:
        #     print(, sheet['properties']['title'])
        return sheet_list

    def get_students_from_list(self, list_name: str) -> list[StudentAndTheme]:
        range = f"{list_name}!A{self.start_row}:B100"

        result = (
            self.sheet.values()
            .get(spreadsheetId=self.sheet_id, range=range)
            .execute()
        )
        # student s
        # theme t
        # group g
        g = list_name
        try:
            result = result["values"]
        except KeyError:
            raise EmptyList(list_name)

        result = [(s, t, g) for s, t in result]

        return result

    def shuffle_students(self, list_groups: list[list[StudentAndTheme]]) -> list[StudentAndTheme]:
        queue: list[StudentAndTheme] = list()

        for current_students in itertools.zip_longest(*list_groups):
            for current_student in current_students:
                if current_student is None:
                    continue
                queue.append(current_student)

        return queue

    def write_query(self, queue: list[StudentAndTheme], list_name=None, list_id=0):

        spreadsheet = self.sheet.get(spreadsheetId=self.sheet_id).execute()
        sheet_list = spreadsheet.get('sheets')
        if list_name is None:
            list_name = sheet_list[list_id]['properties']['title']

        print(f"Запись в лист {list_name}")

        results = self.sheet.values().batchUpdate(spreadsheetId=self.sheet_id, body={
            "valueInputOption": "RAW",
            # Данные воспринимаются, как сырые (не считается значение формул)
            "data": [
                {"range": f"{list_name}!A{self.start_row}:C{len(queue)}",
                 "majorDimension": "ROWS",  # Сначала заполнять строки, затем столбцы
                 "values": queue
                 }
            ]
        }).execute()

        return results

    def main(self):
        try:
            # Call the Sheets API
            result = (
                self.sheet.values()
                .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
                .execute()
            )
            values = result.get("values", [])

            if not values:
                print("No data found.")
                return

            print("Name, Major:")
            for row in values:
                # Print columns A and E, which correspond to indices 0 and 4.
                print(f"{row[0]}, {row[4]}")
        except HttpError as err:
            print(err)


if __name__ == "__main__":
    SAMPLE_SPREADSHEET_ID = "120kLLJRpbZjQofJuPbbB-VtvebMQzG6GLBV24FZGO58"

    s = SheetWrapper(SAMPLE_SPREADSHEET_ID)

    lists = s.get_sheet_lists()
    lists_with_students = lists[1:]

    groups_list = []

    for l in lists_with_students:
        try:
            st_list = s.get_students_from_list(l)
        except EmptyList as e:
            print(e)
            continue
        groups_list.append(st_list)

    quque = s.shuffle_students(groups_list)

    for q in quque:
        print(q)

    s.write_query(quque)

    # print(quque)
