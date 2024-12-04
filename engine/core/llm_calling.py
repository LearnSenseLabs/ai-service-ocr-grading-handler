import requests,json,os
import anthropic
import replicate
import google.generativeai as genai

from engine.core.llm_format_convertion import convert_normal_to_gpt, convert_normal_to_gpt_vision
from engine.gen_utils_files.utils import find_data_in_string

def gpt_vision_calling(messages_vision,model_name='gpt-4-vision-preview'):
    api_key = os.getenv("OPENAI_API_KEY")
    temperature = 0
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model_name,
        "messages":convert_normal_to_gpt_vision(messages_vision),
        "temperature":temperature,
        # "detail":"auto",
        # "max_tokens": 310
    }
    # print(payload)
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    # print(response)
    if response.status_code == 200:
        response =  response.json()
        return {"response":response["choices"][0]["message"]["content"],"statusCode":200}
    elif response.status_code == 503:
        return response.status_code
    else:
        return response.status_code

def gpt_calling(messages,model_name='gpt-4o'):
    temperature = 0
    frequency_penalty = 1
    max_tokens = 800
    # model_name = 'gpt-4o'
    if(len(messages)>0):    
        API_KEY = os.getenv("OPENAI_API_KEY")
        API_ENDPOINT = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        }

        data = {
            "model": model_name,
            "messages": convert_normal_to_gpt(messages),
            "response_format": {"type": "json_object" },
            "temperature": temperature,
            "frequency_penalty":frequency_penalty
        }
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        # print("data going to gpt: ",json.dumps(data))
        
        response = requests.post(API_ENDPOINT,headers=headers, data=json.dumps(data))
        # print(response)
        if response.status_code == 200:
            response = response.json()
            # print("output: ",response)
            response_json = json.loads(response["choices"][0]["message"]["content"])
            gpt_return_json = {
                "aiFeedback":response_json["feedback"],
                "score":float(response_json["score"]),
                "maxScore":float(response_json["maxScore"])
            }
            return {"response":gpt_return_json,"statusCode":200}
        elif response.status_code == 503:
            return response
        elif response.status_code == 400:
            return {"response":"server unreachable","statusCode":400}
        else:
            return response.status_code
    else:
        return {"response":"Please send user data","statusCode":422}

def calude_calling(model_name,reqobj_claude):
    client = anthropic.Anthropic(
            api_key=os.getenv("claude_api_key"),
        )
        # model_name = "claude-3-opus-20240229" if(reqobj['modelName'] == "") else reqobj['modelName']
    message = client.messages.create(
        model=model_name,
        max_tokens=1000,
        temperature=0.1,
        system=reqobj_claude["system"],
        messages=reqobj_claude["messages"],
    )
    if(len(message.content)>0):
        claude_json_response = find_data_in_string(message.content[0].text,"claude-json")
        claude_response = json.loads(claude_json_response)

        claude_response['score'] = float(claude_response['score'])
        claude_response['maxScore'] = float(claude_response['maxScore'])
        claude_statusCode = 200
    else:
        claude_response = {"aiFeedback":"Claude does not found answer","score":0,'maxScore':1}
        claude_statusCode = 400
    return {"statusCode":claude_statusCode,"response":claude_response}
