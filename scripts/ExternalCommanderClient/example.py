"""
Скрипт для извлечения методов и информации о классах из Python-файла
с помощью парсера genslides.task_tools.py_parser.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# === Добавляем корень проекта в sys.path, чтобы можно было импортировать genslides ===
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import genslides.task_tools.commander_client as ComClient

# Импортируем инструменты для продвинутого CLI на Windows
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory

# Ваши шаблоны команд
COMMAND_EXAMPLES = [
    '[{"action":"setCurManTaskByName","kwargs":{"name":""}}]',
    '[{"action": "updateAllnTimes", "kwargs": {"n": 1}}]',
    '[{"action": "updateAllUntillCurrTask", "kwargs": {}}]',
    '[{"action": "update", "kwargs": {}}]',
    'exit',
    'quit'
]

def run_interactive_shell(client: ComClient.ExternalCommanderClient) -> None:
    """8. Интерактивный режим для Windows с автозаполнением на лету через prompt_toolkit."""
    
    # Создаем умный комплитер. 
    # match_middle=True позволяет находить команду, даже если вы ввели "up" или "Task" с середины строки
    # ignore_case=True делает поиск нечувствительным к регистру
    completer = WordCompleter(COMMAND_EXAMPLES, match_middle=True, ignore_case=True)
    
    # Хранилище для истории команд (стрелочки Вверх/Вниз будут работать между вызовами)
    history = InMemoryHistory()

    print("\n" + "="*60)
    print("Запущен продвинутый интерактивный режим (Windows CLI).")
    print("Начните вводить текст (например, 'up' или 'set'), и варианты появятся сами.")
    print("Используйте стрелки [Вверх]/[Вниз] для навигации по подсказкам и истории.")
    print("="*60 + "\n")

    while True:
        try:
            # prompt() заменяет стандартный input(), добавляя автозаполнение и историю
            user_input = prompt(
                "ExtCommander> ", 
                completer=completer, 
                history=history,
                complete_while_typing=True  # Подсказки всплывают прямо во время ввода!
            ).strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit"]:
                print("Выход из интерактивного режима.")
                break

            # Валидация и отправка JSON на сервер
            if user_input.startswith("[") and user_input.endswith("]"):
                try:
                    actions_list = json.loads(user_input)
                    if not isinstance(actions_list, list):
                        print("Ошибка: JSON должен быть массивом объектов [ {...} ]")
                        continue
                except json.JSONDecodeError as je:
                    print(f"Ошибка валидации JSON: {je}")
                    continue
            else:
                actions_list = [{"action": "user_input", "command": user_input}]

            # Отправка в ваш кастомный пайплайн
            execute_custom_pipeline(client, actions_list)
            print("-" * 40)

        except KeyboardInterrupt:
            # Перехват Ctrl+C
            print("\nВыход из интерактивного режима.")
            break
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")

def get_all_sessions(client: ComClient.ExternalCommanderClient) -> List[str]:
    """1. Запрос списка всех доступных сессий."""
    print("--- Запрос списка сессий ---")
    try:
        sessions = client.get_sessions()
        print(f"Доступные сессии на сервере: {sessions}")
        return sessions
    except Exception as e:
        print(f"Ошибка при получении списка сессий: {e}")
        return []


def load_target_session(client: ComClient.ExternalCommanderClient, session_name: str) -> bool:
    """2. Загрузка конкретной сессии по её имени."""
    print(f"--- Загрузка сессии: '{session_name}' ---")
    try:
        res = client.send_genslides_command(cmd_type="load_session", cmd_value=session_name)
        status = res.get("status")
        report = res.get("data", {}).get("report", "No report")
        print(f"Статус загрузки: {status} | Отчет: {report}")
        return status == "ok"
    except Exception as e:
        print(f"Не удалось загрузить сессию '{session_name}': {e}")
        return False

def load_exttree_actioner(client: ComClient.ExternalCommanderClient) -> bool:
    """6. Загрузка актионеров для задач внешнего дерева (ExtTree)."""
    print("--- Загрузка актионеров для ExtTree задач ---")
    try:
        res = client.send_genslides_command(
            cmd_type="load_exttree_actioner", 
            cmd_value=""  # На основе кода сервера, cmd_value здесь не используется
        )
        status = res.get("status")
        report = res.get("data", {}).get("report", "No report")
        print(f"Статус загрузки ExtTree: {status} | Отчет: {report}")
        return status == "ok"
    except Exception as e:
        print(f"Ошибка при выполнении load_exttree_actioner: {e}")
        return False
    
def execute_custom_pipeline(client: ComClient.ExternalCommanderClient, actions_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """7. Отправка пакета кастомных команд на сервер и вывод обновленного состояния."""
    print(f"--- Выполнение пакета кастомных команд ({len(actions_list)} шагов) ---")
    try:
        res = client.send_custom_command(actions=actions_list)
        
        print(f"Статус ответа: {res.get('status')}")
        print(f"Результат (result): {res.get('result')}")
        
        # Выводим новые поля, которые вы добавили в response_data на сервере
        print(f"Текущий актионер (current_actioner): {res.get('current_actioner')}")
        print(f"Доступные актионеры (actioners):\n {"\n".join(["- " + a for a in res.get('actioners')])}")
        
        print("\n[Отчет по текущей задаче (report)]:")
        print(getReportPreview(res.get('report', 'Отчет пуст или отсутствует')))
        
        return res
    except Exception as e:
        print(f"Ошибка при выполнении кастомных команд: {e}")
        return {}


def get_available_actioners(client: ComClient.ExternalCommanderClient) -> Dict[str, Any]:
    """3. Получение списка путей и вариантов всех Актионеров."""
    print("--- Получение списка актионеров ---")
    try:
        res = client.send_genslides_command(cmd_type="get_actioners", cmd_value="")
        data = res.get("data", {})
        print(f"Текущий актионер (value): {data.get('value')}")
        print(f"Доступные варианты (choices): ")
        for value in data.get('choices'):
            print(f" - {value[1]}")
        return data
    except Exception as e:
        print(f"Ошибка при получении актионеров: {e}")
        return {}
    
def getReportPreview( report : dict ):
    if isinstance( report, dict):
        return (
        f"Target: {report.get("name", "None")}\n"
        f"Branch: {report.get("branch", "---")}\n"
        f"Tasks ready: {report.get("frozen",0)} of {report.get("cnt", 0)}\n"
        f"Tree list:{report.get("trees_list",[])}\n"
        f"Current tree:{report.get("curr_tree_name","")}\n"
        f"Current tree branches:{report.get("curr_tree_branches",[])}\n"
    )
    return report
        # report["curr_tree_name"] = gettreenameforradio_trg
        # report["curr_tree_branches"] = man.getBranchEnds()
        # report["trees_list"] = gettreenameforradio_names

def select_active_actioner(client: ComClient.ExternalCommanderClient, actioner_path: str) -> bool:
    """4. Выбор/установка активного Актионера по его пути."""
    print(f"--- Установка активного актионера: '{actioner_path}' ---")
    try:
        res = client.send_genslides_command(cmd_type="set_actioner", cmd_value=actioner_path)
        status = res.get("status")
        report = res.get("data", {}).get("report", "No report")
        print(f"Статус смены актионера: {status} | Отчет: {getReportPreview(report)}")
        return status == "ok"
    except Exception as e:
        print(f"Не удалось установить актионера '{actioner_path}': {e}")
        return False


def select_target_task(client: ComClient.ExternalCommanderClient, actioner_name: str, task_name: str) -> bool:
    """5. Выбор и активация конкретной задачи для указанного Актионера."""
    print(f"--- Выбор задачи '{task_name}' для актионера '{actioner_name}' ---")
    try:
        cmd_payload = {
            "actioner": actioner_name,
            "task": task_name
        }
        res = client.send_genslides_command(cmd_type="set_task", cmd_value=cmd_payload)
        status = res.get("status")
        report = res.get("data", {}).get("report", "No report")
        print(f"Статус активации задачи: {status} | Отчет: {report}")
        return status == "ok"
    except Exception as e:
        print(f"Ошибка при выборе задачи '{task_name}': {e}")
        return False


def make_completer(vocabulary: List[str]):
    """Фабрика для создания функции автозаполнения."""
    def completer(text: str, state: int) -> Optional[str]:
        # Ищем совпадения по началу введенного текста (регистронезависимо)
        options = [cmd for cmd in vocabulary if cmd.lower().startswith(text.lower())]
        if state < len(options):
            return options[state]
        return None
    return completer

def main():
    parser = argparse.ArgumentParser(description="Скрипт автоматизации для ExternalCommander API.")
    parser.add_argument(
        "--url", 
        type=str, 
        default="http://localhost", 
        help="Базовый URL сервера (по умолчанию: http://localhost)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Порт FastAPI сервера (по умолчанию: 8000)"
    )
    
    args = parser.parse_args()
    
    # Собираем полный адрес и инициализируем клиент
    server_address = f"{args.url}:{args.port}"
    print(f"Подключение к серверу ExternalCommander по адресу: {server_address}\n")
    client = ComClient.ExternalCommanderClient(base_url=server_address)

    # Последовательно выполняем все этапы пайплайна
    sessions = get_all_sessions(client)
    # print()

    if not sessions:
        print("Список сессий пуст или сервер недоступен. Завершение работы.")
        sys.exit(1)

    # # Имитируем логику: берем первую сессию из списка для демонстрации
    # target_session = sessions[0]
    target_session = "archi_helper_v1"
    if not load_target_session(client, target_session):
        sys.exit(1)
    # print()

    actioners_data = get_available_actioners(client)
    # print()

    choices = actioners_data.get("choices", [])
    if choices:
        # Берём первый доступный путь актионера для теста
        target_actioner_path = "base_router_v1"
        if not select_active_actioner(client, target_actioner_path):
            sys.exit(1)
        print()

        if not load_exttree_actioner(client):
            sys.exit(1)

        run_interactive_shell(client)


if __name__ == "__main__":
    main()