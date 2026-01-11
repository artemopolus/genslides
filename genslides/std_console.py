# std_console.py
import genslides.commanager.ext as ExtComm

def startSimpleCommander(host: str = "127.0.0.1", port: int = 8000):
    """
    Создаёт ExternalCommander и стартует встроенный HTTP сервер.
    Возвращает экземпляр команды для дальнейшего управления.
    """
    projecter = ExtComm.ExternalCommander()
    projecter.start_server(host=host, port=port)
    return projecter
