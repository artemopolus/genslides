import uuid
import secrets
import datetime
from typing import Union

# Константа: число 100-нс интервалов между 1582-10-15 и 1970-01-01
_UUID_EPOCH_100NS = 122192928000000000

def generateKey(filename_safe: bool = True) -> str:
    """
    Генерирует UUID v1 с случайным node (без реального MAC), но сохраняет таймстамп.
    - filename_safe=True -> возвращает compact hex (32 символа), удобно для файлов/имен.
    - filename_safe=False -> возвращает стандартную строку UUID с дефисами.

    В соответствии с RFC, мы ставим multicast-бит в node, чтобы явно указать, что
    это не MAC-адрес (без утечки аппаратных данных).
    """
    # random 48-bit value
    node = secrets.randbits(48)
    # установить multicast бит (LSB первой октеты) чтобы указать "не-MAC" (RFC 4122 recommendation)
    node |= (0x01 << 40)  # 0x01 << 40 == 0x010000000000
    u = uuid.uuid1(node=node)
    return u.hex if filename_safe else str(u)


def extractTimeFromKey(key: Union[str, uuid.UUID]) -> datetime.datetime:
    """
    Извлекает время (UTC) из UUIDv1, возвращая timezone-aware datetime в UTC.
    Принимает:
      - компактную hex-строку (32 символа),
      - стандартную строку с дефисами,
      - объект uuid.UUID.
    Бросает ValueError если передан не UUIDv1.
    """
    # Преобразуем в uuid.UUID (поддерживает и 32-символьный hex и стандартную форму)
    if isinstance(key, uuid.UUID):
        u = key
    else:
        try:
            u = uuid.UUID(key)
        except Exception as e:
            raise ValueError(f"Не удалось разобрать переданный ключ как UUID: {e}")

    if u.version != 1:
        raise ValueError("Переданный UUID не версии 1 — в нём нет временного поля.")

    ts_100ns = u.time  # количество 100нс интервалов с эпохи 1582-10-15
    # переводим в секунды от unix-эпохи
    unix_seconds = (ts_100ns - _UUID_EPOCH_100NS) / 10_000_000
    return datetime.datetime.fromtimestamp(unix_seconds, tz=datetime.timezone.utc)

