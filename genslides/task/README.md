Each of task below have one input: prompt. Each task below can have parent then message chain of task is message chain of its parent plus messages of its own. Each task can be linked to CollectTask. Task can have params.
Name of task consist of task type plus "Task".
RequestTask is task that can create one message of chain of messages between user as user and assistant (like ChatGPT).
ResponseTask is task that can send chain of messages to get answer of assistant (like ChatGPT) and add response to chain of messages. 
WebSurfTask is task that get prompt as request to search engine (like Google Search) and create 10 ReadPageTask based on url from search engine. This task has web_request in params which is request for search engine.
ReadPageTask get data from webpage based on url from prompt and add thsi data to chain of messages.
WriteToFileTask write data from last message of message chain to path from prompt. This task has path_to_write in params as path to file to write.
ReadFileTask read data from file by path from prompt and add this data to message chain.. This task has path_to_read in params as path to file to read.
CollectTask is task that get data from linked task and add it in message chain.