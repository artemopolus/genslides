
"""
Реализация KeyCraftTask для работы с MCPClient через AsyncRunner.
Использует два последовательных вызова updateIternal:
 1) Подключение и очередь запросов;
 2) Проверка результатов: если не готовы — повторная проверка в следующем вызове;
    иначе — вывод результатов, очистка, и возврат к начальному шагу.
"""
from genslides.task.text import TextTask, TaskDescription
from genslides.mcp.mcpclient import MCPClient
import copy
import asyncio

class MCPTask(TextTask):
    def __init__(self, task_info : TaskDescription):
        super().__init__(task_info, type="MCP")
        pair = {}
        pair["role"] = task_info.prompt_tag
        pair["content"] = self.getRichPrompt()

        tmp_msg_list = self.msg_list.copy()
        tmp_msg_list.append(pair)
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list, remove_last=False)
        del tmp_msg_list
        
        if len(msg_list_from_file) == 0:
            self.msg_list.append(pair)
            self.onEmptyMsgListAction()
        else:
            self.onExistedMsgListAction(msg_list_from_file)

    def onEmptyMsgListAction(self):
        self.saveJsonToFile(self.msg_list)
        return super().onEmptyMsgListAction()

    def onExistedMsgListAction(self, msg_list_from_file):
        self.msg_list = msg_list_from_file
        return super().onExistedMsgListAction(msg_list_from_file)


    def updateIternal(self, input : TaskDescription =None):
        cres, cparam = self.getParamStruct("mcp_config", only_current=True)
        mres, mparam = self.getParamStruct("model")
        messages = self.getParent().getMsgs()

        if not cres or not mres:
            return None
        
        cparam = self.convParamStruct(copy.deepcopy(cparam))
        mparam = self.convParamStruct(copy.deepcopy(mparam))

        if cparam.get("block", False):
            self._execute_block(messages, cparam, mparam)
            return super().updateIternal(input)
        else:
            self.updateUpdationInfo("No non-blocking task now")
        return None


    def _execute_block(self, messages : list[dict], mcp_params : dict, model_params : dict):
        """
        Блокирующее выполнение: подключение, обработка, очистка.
        """
        def _run_mcp_client_server():
            async def blocking_mcp_main():
                client = MCPClient()
                await client.connect_to_server(mcp_params.get("path_to_server",""))
                proc_res, response, outparams = await client.process_query(messages, model_params)
                await client.cleanup()
                return proc_res, response, outparams
            return asyncio.run(blocking_mcp_main())
        
        self.updateUpdationInfo(f"Execute blocking call")

        process_result, tool_call_output, tool_call_options = _run_mcp_client_server()
        if process_result:
            tool_call_options["type"] = self.getType()
            tool_call_options["result"] = tool_call_output
            self.setParamStruct(tool_call_options)

