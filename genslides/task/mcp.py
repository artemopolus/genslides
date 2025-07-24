
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
import json

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
            if not self.checkParentMsgList(update=True, save_curr=False):
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
                text = ""
                await client.connect_to_server(mcp_params.get("path_to_server",""))
                if mcp_params.get("use_json", False):
                    proc_res, response, outparams = await client.process_query_with_so(messages, model_params, mcp_params)

                    jsonkeyspath = mcp_params.get("jsonkeyspath","json_schema,schema,properties,tool_calls,properties")
                    iresp = json.loads(response)

                    jsonkeyspath_tags = jsonkeyspath.split(",")

                    tool_calls_tag = "tool_calls" if len(jsonkeyspath_tags) < 2 else jsonkeyspath_tags[-2]

                    if tool_calls_tag in iresp:
                        tools_call_res = []
                        for key, value in iresp[tool_calls_tag].items():
                            tool_output = await client.session.call_tool(key, value)
                            tool_output_txt = tool_output.content[0].text
                            tools_call_res.append({
                                "name": key,
                                "arguments": value,
                                "output": tool_output_txt
                            })
                            text += tool_output_txt
                            iresp[tool_calls_tag][key]["output"] = tool_output_txt
                        outparams["tool_outputs"] = tools_call_res
                        outparams["tool_output_final_text"] = text
                        # iresp["tool_outputs"] = tools_call_res
                    response = json.dumps( iresp, indent = 3, ensure_ascii=False) 
                else:
                    proc_res, response, outparams = await client.process_query(messages, model_params)
                    if "tool_calls" in outparams:
                        for tool in outparams["tool_calls"]:
                            tool_output = await client.session.call_tool(tool["name"], tool["arguments"])
                            text += tool_output.content[0].text
                        outparams["tool_output"] = text
                await client.cleanup()
                return proc_res, response, outparams
            return asyncio.run(blocking_mcp_main())
        
        self.updateUpdationInfo(f"Execute blocking call")

        process_result, tool_call_output, tool_call_options = _run_mcp_client_server()
        if process_result:
            self.updateUpdationInfo("Succesfull run mcp")
            self.appendMessage({"role":"assistant","content": tool_call_output})
        else:
            self.freezeTask()
            self.updateUpdationInfo("Error on MCP")
        if process_result:
            tool_call_options["type"] = self.getType()
            tool_call_options["result"] = tool_call_output
            self.setParamStruct(tool_call_options)

    def forceCleanChat(self):
        self.msg_list = []
        self.saveAllParams()
        self.freezeTask()
        return super().forceCleanChat()

