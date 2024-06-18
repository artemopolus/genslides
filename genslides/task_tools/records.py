

def getPackForRecord(role: str, content : str, task_name : str) -> dict:
    return {
                "role": role, 
                "content": content,
                "task": task_name
}

