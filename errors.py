class EmptyList(ValueError):
    def __init__(self, list_name):
        super().__init__(f"Лист {list_name} пустой!")