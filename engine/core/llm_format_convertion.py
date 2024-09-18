import base64,httpx

def convert_normal_to_gpt(message):
    updated_gpt_data = []
    
    # for message in normal_data:
    if(message.__contains__('systemPrompt')):
        updated_gpt_data.append({
            "role": "system",
            "content": message['systemPrompt']
        })
    # if(message.__contains__('Rubric')):
    if(message.__contains__('rubric')):
        updated_gpt_data.append({
            "role": "system",
            "content": message['rubric']
            # "content": message['Rubric']
        })
    # if(message.__contains__('Question')):
    if(message.__contains__('question')):
        updated_gpt_data.append({
            "role": "system",
            "content": str("question: "+message['question'])
        })
    # if(message.__contains__('answer')):
    if(message.__contains__('studentAnswer')):
        updated_gpt_data.append({
            "role": "user",
            "content": str("studentAnswer: "+str(message['answer'])) if(str(message['answer'])!="") else "No Answer"
        })
        # print(message)
    return updated_gpt_data
def convert_gpt_to_gemini(gpt_data):
    gemini_data = {
        "messages":[]
    }
    for message in gpt_data:
        if message["role"] == "system":
            gemini_data["messages"].append({
                "role": "user",
                "parts": "System: " + message["content"]
            })
        elif message["role"] == "user":
            gemini_data["messages"].append({
                "role": "user",
                "parts": message["content"]
            })

    return gemini_data
def convert_gpt_to_claude(gpt_data):
    claude_data = {
        "system": "",
        "messages": []
    }
    combined_user_data = ""
    for message in gpt_data:
        if message["role"] == "system":
            claude_data["system"] += message["content"].strip() + "\n\n"
        elif message["role"] == "user":
            # claude_data["messages"].append({
            #     "role": "user",
            #     "content": [{"text": message["content"], "type": "text"}]
            # })
            combined_user_data += message["content"]+"," 

    claude_data["system"] = claude_data["system"].strip()
    claude_data["messages"] =[{"role":"user","content":[{"text": combined_user_data, "type": "text"}]}]
    return claude_data

def convert_gpt_to_llamma(gpt_data):
    llamma_data = {
        "system": "",
        "prompt": "",
    }
    combined_user_data = ""
    for message in gpt_data:
        if message["role"] == "system":
            llamma_data["system"] += message["content"].strip() + "\n\n"
        elif message["role"] == "user":
            combined_user_data += message["content"]+"," 

    llamma_data["system"] = llamma_data["system"].strip()
    llamma_data["prompt"] = combined_user_data
    return llamma_data

def convert_gpt_to_gemini(gpt_data):
    gemini_data = {
        "system": "",
        "messages": []
    }
    combined_user_data = ""
    for message in gpt_data:
        if message["role"] == "system":
            gemini_data["system"] += message["content"].strip() + "\n\n"
        elif message["role"] == "user":
            # claude_data["messages"].append({
            #     "role": "user",
            #     "content": [{"text": message["content"], "type": "text"}]
            # })
            combined_user_data += message["content"]+"," 

    gemini_data["system"] = gemini_data["system"].strip()
    gemini_data["messages"] =[{"role":"user","parts":[combined_user_data]}]
    return gemini_data

def convert_normal_to_gpt_vision(message,model_class="openai-ocr"):
    updated_gpt_vision_data = []
    image_url_json = {}
    # if(isinstance(message['answer'],list)):
    #     for answer_list in range(0,len(message['answer'])):
    #         image_url_json["image_url"+str(i+1)] = message['answer'][i]
    # else:
    #     image_url_json = {
    #         'type':'image_url',
    #         'image_url':message['answer']
    #     }
    
    # if(model_class=="gpt-ocr"):
    if(model_class=="openai-ocr" or model_class=="gpt-ocr"):
    # for message in normal_data:
        if(message.__contains__('systemPrompt') and message.__contains__('answer')):
            updated_gpt_vision_data.append({
                "role": "user",
                "content": [
                    {
                        "type":"text",
                        "text":message['systemPrompt']
                    },
                    {
                        "type":"image_url",
                        # "image_url":{"url":message['answer'][0] if(isinstance(message['answer'],list)) else message['answer']}
                        "image_url":{"url":message['answerUrl'] if(isinstance(message['answerUrl'],str)) else ""}
                    }
                ]
            })
    else:
        if(message.__contains__('systemPrompt') and message.__contains__('answer')):
            updated_gpt_vision_data.append({
                "role": "user",
                "content": [
                    {
                        "type":"text",
                        "text":message['systemPrompt']+", Question: "+message['question']+" ,"+message['rubric']
                    },
                    {
                        "type":"image_url",
                        # "image_url":{"url":message['answer'][0] if(isinstance(message['answer'],list)) else message['answer']}
                        "image_url":{"url":message['answerUrl'] if(isinstance(message['answerUrl'],str)) else ""}
                    }
                ]
            })
    return updated_gpt_vision_data

def convert_normal_to_claude_vision(message, model_class="claude-vision"):
    updated_claude_vision_data = []

    if model_class == "claude-vision":
        # if 'systemPrompt' in message and 'user_image' in message:
        #     image_data = message['user_image']
        #     if isinstance(image_data, str) and image_data.startswith('http'):
        #         image_url = image_data
        #     else:
        #         raise ValueError("Image data must be a valid URL.")
        if(message.__contains__('systemPrompt')):
            image_url = message['answer'][0] if(isinstance(message['answer'],list)) else message['answer']
            updated_claude_vision_data.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message['systemPrompt']
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/webp",
                            "data": base64.b64encode(httpx.get(image_url).content).decode("utf-8"),
                    },
                }
                ]
            })
    return updated_claude_vision_data   