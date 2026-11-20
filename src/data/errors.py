class DataError(Exception):
    """Базовая ошибка слоя данных; текст сообщения можно показывать пользователю."""


class StorageError(DataError):
    pass


class ValidationError(DataError):
    pass


class EntryNotFound(DataError):
    pass


class VaultNotInitialized(DataError):
    pass


class VaultAlreadyInitialized(DataError):
    pass


class WrongMasterPassword(DataError):
    pass
