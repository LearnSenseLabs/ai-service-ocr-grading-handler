import requests,json,os
import anthropic
import ast
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content

from engine.core.llm_format_convertion import convert_normal_to_gpt, convert_normal_to_gpt_vision
from engine.gen_utils_files.utils import assign_rubric_id_to_response, find_data_in_string

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
        response = response.json()
        return {"response":response["choices"][0]["message"]["content"],"statusCode":200}
    elif response.status_code == 503:
        return response.status_code
    else:
        return response.status_code

def gpt_calling(messages,model_name='gpt-4o'):
    temperature = 0
    frequency_penalty = 1
    max_tokens = 1000
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
            "top_p": 1,
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
            # gpt_return_json = {
            #     "aiFeedback":response_json["overallFeedback"],
            #     "score":float(response_json["score"]),
            #     "maxScore":float(response_json["maxScore"])
            # }
            rubricWiseResponse,calculated_score,max_score = assign_rubric_id_to_response(rubric_json=messages["rubricJson"],response_json=response_json["rubricWiseResponse"])
            gpt_return_json = {
                "aiFeedback":response_json["overallFeedback"],
                "score":calculated_score,
                "maxScore":max_score,
                "rubricWiseResponse":rubricWiseResponse
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

def gemini_calling(reqobj_gemini):
    genai.configure(api_key=os.getenv("GENAI_API_KEY"))
    model_name = "gemini-1.5-pro"
    print("gemini request started...")
    # Create the model
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1200,
    "response_schema": content.Schema(
        type = content.Type.OBJECT,
        enum = [],
        required = ["response"],
        properties = {
        "response": content.Schema(
            type = content.Type.OBJECT,
            enum = [],
            required = ["feedback", "score", "maxScore"],
            properties = {
            "feedback": content.Schema(
                type = content.Type.STRING,
            ),
            "score": content.Schema(
                type = content.Type.INTEGER,
            ),
            "maxScore": content.Schema(
                type = content.Type.INTEGER,
            ),
            },
        ),
        },
    ),
    "response_mime_type": "application/json",
    }

    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
        system_instruction=reqobj_gemini["system"],
    )

    chat_session = model.start_chat()
    # print(reqobj_gemini['messages'][0]['parts'][0])
    response = chat_session.send_message("student Answer: "+reqobj_gemini['messages'][0]['parts'][0])
    # print("gemini response: ",response)
    # print("gemini response text: ",response.text)

    if(response.text is not None):
        gemini_response = json.loads(response.text)
        gemini_return_json = {
            "aiFeedback":gemini_response['response']['feedback'],
            "score":float(gemini_response['response']['score']),
            "maxScore":float(gemini_response['response']['maxScore'])
        }
        # print(gemini_return_json)
        gemini_statusCode = 200
    else:
        gemini_response = {"aiFeedback":"Gemini does not found answer","score":0,'maxScore':1}
        gemini_statusCode = 400

    return {"statusCode":gemini_statusCode,"response":gemini_return_json}

def gemini_vision_number_runner(batch_size,encoded_image_base64):

    genai.configure(api_key=os.getenv("GENAI_API_KEY"))
    # Create the model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1000,
        "response_mime_type": "text/plain",
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        system_instruction=f"Perform OCR on an image where each number is enclosed in a separate box and there are {batch_size} boxes. Ensure that the OCR system accurately recognizes each number, accounting for potential variations in handwriting, such as faint or broken strokes, or digits that may look similar. Pay particular attention to capturing each digit precisely, avoiding common misinterpretations (e.g., confusing '3' with '5,' '8' with '0,' or '4' with '6'). Each box's recognized number should be provided in list like: [contentOfBox1,contentOfBox2,....], and do not miss any box, and if there is not any number available then, give it empty like: [contentOfBox1,'',...] here box2 has an empty response. Please do not give any introductory statements.",
    )
    
    try:
        response = model.generate_content(["Please give ocr for this image: ",encoded_image_base64])
        print(response.text)
        return {"response":ast.literal_eval(response.text),"statusCode":200}
    except Exception as e:
        print(f"Error in gemini_runner: {e}")
        return {"response":f"Error in gemini_runner: {e}","statusCode":500}
