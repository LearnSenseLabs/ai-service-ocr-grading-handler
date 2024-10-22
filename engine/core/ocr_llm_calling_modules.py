'''
Modules to be added
openai-ocr
openai-ocr-essay
openai-mcq-ocr
anthropic-ocr
antropic_ocr_electricity
anthropic-ocr-maths
anthropic-ocr-maths-geo
anthropic-ocr-maths-frac
'''
import requests,json,os
import anthropic
import replicate
import google.generativeai as genai

from engine.core.llm_format_convertion import convert_gpt_to_claude, convert_normal_to_claude_vision, convert_normal_to_gpt, convert_normal_to_gpt_vision
from engine.gen_utils_files.utils import convert_rubric_to_string, find_data_in_string

def openai_ocr(user_image,system_prompt="",description='',model_name='gpt-4o',lang='english'):
    # messages_vision,model_name='gpt-4-vision-preview'):
    api_key = os.getenv("OPENAI_API_KEY")
    temperature = 0
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    messages_vision = {"systemPrompt":system_prompt,"user_image":user_image}
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


def claude_vision_calling(user_image,system_prompt,model_name="claude-3-5-sonnet-20240620", lang="eng"):
    client = anthropic.Anthropic(
        api_key=os.getenv("claude_api_key"),
    )
    reqobj_claude = {"systemPrompt":system_prompt,"answer":user_image}
    messages_ocr = convert_normal_to_claude_vision(reqobj_claude)
    
    message = client.messages.create(
        model=model_name,
        max_tokens=1000,
        temperature=0,
        system=reqobj_claude["systemPrompt"],
        messages=messages_ocr,
    )
    
    if message.content:
        # claude_json_response = find_data_in_string(message.content[0].text,"claude-json")
        # claude_response = json.loads(claude_json_response)
        claude_json_response = message.content[0].text
        if(isinstance(claude_json_response,str)):
            claude_response = claude_json_response
        else:
            claude_response = json.loads(claude_json_response)
        # claude_response['score'] = float(claude_response['score'])
        # claude_response['maxScore'] = float(claude_response['maxScore'])
        claude_statusCode = 200
    else:
        response = {"ocr": ""}
        ocr_statusCode = 400
    
    return {"statusCode": claude_statusCode, "response": claude_response}
def openai_scoring(student_answer,maxScore,rubrics,question,system_prompt="",model_name="gpt-4o",lang="english"):
    # messages,model_name='gpt-4o'):    
    system_prompt = ""+maxScore
    temperature = 0
    frequency_penalty = 1
    max_tokens = 400
    messages_openai_scoring = {"systemPrompt":system_prompt,"studentAnswer":student_answer,
                               "question":question,"rubrics":convert_rubric_to_string(rubrics)}
    # model_name = 'gpt-4o'
    if(len(messages_openai_scoring)>0):    
        API_KEY = os.getenv("OPENAI_API_KEY")
        API_ENDPOINT = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        }

        data = {
            "model": model_name,
            "messages": convert_normal_to_gpt(messages_openai_scoring),
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

def anthropic_scoring(student_answer,maxScore,rubrics,question,system_prompt="",model_name="claude-3-5-sonnet-20240620",lang="english"):
    client = anthropic.Anthropic(
            api_key=os.getenv("claude_api_key"),
        )
    # model_name = "claude-3-opus-20240229" if(reqobj['modelName'] == "") else reqobj['modelName']
    
    messages_antropic_scoring = {"systemPrompt":system_prompt+maxScore,"studentAnswer":student_answer,
                               "question":question,"rubrics":convert_rubric_to_string(rubrics)}
    
    reqobj_claude = convert_gpt_to_claude(convert_normal_to_gpt(messages_antropic_scoring))
    
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
