from openai import OpenAI
from openai import OpenAIError
from openai import AuthenticationError, InternalServerError
from parser import Config
from duckduckgo_search import DDGS
import json
import traceback

clientAI = OpenAI(base_url=Config.base_url, api_key=Config.key)

def list_models():
    try:
        return clientAI.models.list()
    except AuthenticationError:
        print("Failed to authenticate to api")
        return False
    except InternalServerError:
        print("API has no metadata")
        return [None]
    
def optimize_history(instructions: str, context: list[dir]):
    # instructions.format(
    #     instruction=original_instruction
    # ) 
    improved_context = []
    for each in context:
        temp = {"role": None, "content": None}
        speaker = "other person" if each['role'] == "assistant" else "user" 
        temp["content"] = f"[{speaker}] {each['content']}"
        temp["role"] = f"user"
        improved_context.append(temp)
        messages = [
            {"role": "system", "name": "instructions", "content": instructions},
            *context,
            # {"role": "user", "content": f"[Summarize the roleplay. Make sure only important detail is preserved. Do not write about anything that happens before or after the roleplay transcript or make anything up, only write your summary about those messages in the transcript. Do not indicate your role in the roleplay. And keep it brief as a summary.]"}
        ]
    response = clientAI.chat.completions.create(
            model=Config.base_url,
            messages=messages,
            max_tokens=512,
            temperature=0
        )
    try:
        response_message = response.choices[0].message.content
    except AttributeError as e:
        return False
    new_history = {"role": "user", "content": response_message}
    return new_history

def generate_response(instructions, history, stream=False):
    messages = [
            {"role": "system", "name": "instructions", "content": instructions},
            *history,
        ]
    try:
        response = clientAI.chat.completions.create(
            model=Config.model,
            messages=messages,        
            max_completion_tokens=Config.max_token,
            temperature=Config.temperature,
            stream=stream
        )
        if stream:
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    print(chunk.choices[0].delta.content, end="")
                print(chunk)
        response_message = response.choices[0].message
        # print("The response raw: ", response_message)
    except OpenAIError as e:
        return traceback.format_exc(), False
    except AttributeError as e:
        return traceback.format_exc(), False
    if stream:
        return response_message, True
    return response_message.content, True

def duckduckgotool(query) -> str:
    if Config.internet_access:
        return "internet access has been disabled by user"
    blob = ''
    results = DDGS(proxy=None).text(query, max_results=6)
    try:
        for index, result in enumerate(results[:6]):  # Limiting to 6 results
            blob += f'[{index}] Title : {result["title"]}\nSnippet : {result["body"]}\n\n\n Provide a cohesive response base on provided Search results'
    except Exception as e:
        print("Error:", e)
        blob += f"Search error: {e}\n"
    return blob