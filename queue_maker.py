import itertools
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from enums import Mark
from errors import EmptyList

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

StudentAndTheme = tuple[str, str, str]  # [Имя студента, Тема, Группа студента]
COUNT_STUDENT_FIELDS = 3  # count str in StudentAndTheme
RangeDict = dict[str, str]  # Словарь с указанием диапазона


class SheetWrapper:
    def __init__(self, sheet_id: str, use_titles=True, list_name=None, list_id=0):
        self.sheet_id = sheet_id
        self.start_row_idx = 1 if use_titles else 0
        self._student_num = 0

        # set up connection
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

        # sheet
        self.sheet = service.spreadsheets()

        self.main_list_id = 0

    def get_sheet_lists_titles(self) -> list[str]:
        """
        Получить названия всех листов в таблице
        """

        spreadsheet = self.sheet.get(spreadsheetId=self.sheet_id).execute()
        sheet_list = spreadsheet.get("sheets")
        sheet_list = [s["properties"]["title"] for s in sheet_list]
        return sheet_list

    def get_students_sheets(self):
        """
        Получить названия всех листов в таблице кроме первого (т.е. получить названия листов только со студентами
        """
        return self.get_sheet_lists_titles()[1:]

    def get_students_from_list(self, list_title: str) -> list[StudentAndTheme]:
        """
        Получить всех студентов из листа

        :param list_title:
        :return:
        """
        start_col, start_row = 0, self.start_row_idx
        end_col, end_row = 1, 100
        range = self._generate_range(start_col, start_row, end_col, end_row)

        result = self._read_cells(range, list_title=list_title)

        # student -> s
        # theme -> t
        # group -> g
        g = list_title
        result = [(s, t, g) for s, t in result]

        return result

    def shuffle_students(
        self, list_groups: list[list[StudentAndTheme]]
    ) -> list[StudentAndTheme]:
        """
        Получает на вход список списков студентов и создаёт из них очередь путём перемешивания их

        :param list_groups:
        :return:
        """
        queue: list[StudentAndTheme] = list()

        for current_students in itertools.zip_longest(*list_groups):
            for current_student in current_students:
                if current_student is None:
                    continue
                queue.append(current_student)

        return queue

    def write_queue(self, queue: list[StudentAndTheme]):
        """
        Записать очередь в таблицу (в 1й лист)

        :param queue:
        :return:
        """
        print(f"Запись в лист {self.main_list_id}")

        start_col, start_row = 0, self.start_row_idx
        end_col, end_row = COUNT_STUDENT_FIELDS, len(queue) + self.start_row_idx

        range = self._generate_range(start_col, start_row, end_col, end_row)

        self._write_cells(range, queue, is_single=False)

    def get_next_student(self, offset: int = 0) -> StudentAndTheme | None:
        student_num = self._student_num + offset
        range = self._get_student_range(student_num)

        try:
            result = self._read_cells(range)
            result = result[0]
        except (EmptyList, KeyError) as e:
            return None
        result = result[:COUNT_STUDENT_FIELDS]

        return result

    def mark_current_student(self, mark: Mark, comment: str = None):
        """
        Поставить отметку студенту, который сейчас идёт по очереди

        :param mark: оценка, объект enum'а
        :param comment: коммантарий, который будет записан в поле с оценкой (можно отсавить пустым)
        :return:
        """
        print(f"Запись в лист {self.main_list_id}")

        range = self._get_student_mark_range(self._student_num)

        color = mark.value

        if comment is not None:
            self._write_cells(range, comment)

        self._update_cell_color(range, *color)

    def set_queue(self, idx=0):
        """
        Установить какой сейчас студент по счёту выступает

        :param idx:
        :return:
        """
        self._student_num = idx

    def increment_queue(self, count: int = 1):
        """
        Установить следующего студента выступающим

        :return:
        """
        self._student_num += count

    ########################### range func ->

    def _convert_to_a1(self, range: RangeDict, list_title=None):
        """
        Конвертация дикта RangeDict в A1 нотацию

        :param range:
        :param list_title:
        :return:
        """
        s_col = int(range["startColumnIndex"])
        s_row = int(range["startRowIndex"])
        e_col = int(range["endColumnIndex"])
        e_row = int(range["endRowIndex"])

        #         name = self.sheet_list[name]
        s_col = chr(s_col + 65)
        s_row += 1
        e_col = chr(e_col + 65)
        e_row += 1

        range = f"{s_col}{s_row}:{e_col}{e_row}"

        if list_title is not None:
            return f"{list_title}!{range}"
        else:
            return f"{range}"

    def _get_student_range(self, student_num) -> RangeDict:
        """
        Получает на вход номер студента и выдаёт диапазон ячеек, в котором он находится

        :param student_num:
        :return:
        """
        start_row, end_row = (
            student_num + self.start_row_idx,
            student_num + self.start_row_idx,
        )
        start_col, end_col = 0, COUNT_STUDENT_FIELDS

        return self._generate_range(start_col, start_row, end_col, end_row)

    def _get_student_mark_range(self, student_num) -> RangeDict:
        """
        Получает на вход номер студента и выдаёт диапазон ячеек, в котором находитяс его поле с оценкой

        :param student_num:
        :return:
        """
        start_row, end_row = (
            student_num + self.start_row_idx,
            student_num + self.start_row_idx + 1,
        )
        start_col, end_col = COUNT_STUDENT_FIELDS, COUNT_STUDENT_FIELDS + 1

        return self._generate_range(start_col, start_row, end_col, end_row)

    def _generate_range(self, start_col, start_row, end_col, end_row) -> RangeDict:
        """
        Чисто метод по кайфу, создаёт объект RangeDict

        :param start_col:
        :param start_row:
        :param end_col:
        :param end_row:
        :return:
        """
        range = {
            "sheetId": self.main_list_id,
            "startColumnIndex": start_col,
            "startRowIndex": start_row,
            "endColumnIndex": end_col,
            "endRowIndex": end_row,
        }
        return range

    ########################### range func <-

    ########################### requests func ->

    def _update_cell_color(self, range: RangeDict, red, green, blue):
        """
        Обновляет цвет клетки(-ок) в range

        :param range:
        :param red:
        :param green:
        :param blue:
        :return:
        """
        self.sheet.batchUpdate(
            spreadsheetId=self.sheet_id,
            body={
                "requests": [
                    {
                        "repeatCell": {
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {
                                        "red": red,
                                        "green": green,
                                        "blue": blue,
                                    }
                                }
                            },
                            "range": range,
                            "fields": "userEnteredFormat",
                        }
                    }
                ]
            },
        ).execute()

    def _write_cells(self, range: RangeDict, value, is_single=True):
        """
        Записывает значения в клетки

        :param range:
        :param value:
        :param is_single:
        :return:
        """
        if is_single:
            value = [[value]]

        range = self._convert_to_a1(range)

        results = (
            self.sheet.values()
            .batchUpdate(
                spreadsheetId=self.sheet_id,
                body={
                    "valueInputOption": "RAW",
                    # Данные воспринимаются, как сырые (не считается значение формул)
                    "data": [
                        {
                            "range": range,
                            "majorDimension": "ROWS",  # Сначала заполнять строки, затем столбцы
                            "values": value,
                        }
                    ],
                },
            )
            .execute()
        )
        return results

    def _read_cells(self, range: RangeDict, list_title: str = None) -> list:
        """
        Выдаёт значения клеток из range

        :param range:
        :param list_title:
        :return:
        """
        range = self._convert_to_a1(range, list_title=list_title)

        result = (
            self.sheet.values().get(spreadsheetId=self.sheet_id, range=range).execute()
        )
        try:
            result = result["values"]
        except KeyError:
            raise EmptyList(list_title or "<First list>")

        return result

    ########################### requests func <-


if __name__ == "__main__":
    SAMPLE_SPREADSHEET_ID = "120kLLJRpbZjQofJuPbbB-VtvebMQzG6GLBV24FZGO58"

    s = SheetWrapper(SAMPLE_SPREADSHEET_ID)

    lists_with_students = s.get_students_sheets()

    groups_list = []

    for l in lists_with_students:
        try:
            st_list = s.get_students_from_list(l)
        except EmptyList as e:
            print(e)
            continue
        groups_list.append(st_list)

    quque = s.shuffle_students(groups_list)
    s.write_queue(quque)

    print("Записаны студенты")

    # test data
    marks = [
        Mark.good,
        Mark.good,
        Mark.good,
        Mark.good,
        Mark.good,
        Mark.middle,
        Mark.middle,
        Mark.middle,
        Mark.middle,
        Mark.bad,
        Mark.nothing,
        Mark.nothing,
    ]
    comments = [
        "доработать проект",
        "возьму на заметку",
        "молодец!",
        "недожал",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ]

    # process imitation
    import random

    next_st = s.get_next_student()
    while next_st is not None:
        cur_st = next_st
        next_st = s.get_next_student(1)

        print(f"Рассказывает студент: {cur_st}")
        if next_st:
            print(f"Готовится студент: {next_st}")

        mark = random.choice(marks)
        s.mark_current_student(mark, comment=random.choice(comments))
        print(f"Поставлена оценка: {mark}")
        s.increment_queue()

    pass
