def convert_normal_to_gpt(message):
    updated_gpt_data = []
    
    # for message in normal_data:
    if(message.__contains__('systemPrompt')):
        updated_gpt_data.append({
            "role": "system",
            "content": message['systemPrompt']
        })
    if(message.__contains__('Rubric')):
        updated_gpt_data.append({
            "role": "system",
            "content": message['Rubric']
        })
    if(message.__contains__('Question')):
        updated_gpt_data.append({
            "role": "system",
            "content": str("Question: "+message['Question'])
        })
    if(message.__contains__('answer')):
        updated_gpt_data.append({
            "role": "user",
            "content": str("Answer: "+str(message['answer'])) if(str(message['answer'])!="") else "No Answer"
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

def convert_normal_to_gpt_vision(message,model_class="gpt-ocr"):
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
    if(model_class=="gpt-ocr"):
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
                        "image_url":{"url":message['answer'][0] if(isinstance(message['answer'],list)) else message['answer']}
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
                        "text":message['systemPrompt']+", Question: "+message['question']+" ,"+message['Rubric']
                    },
                    {
                        "type":"image_url",
                        "image_url":{"url":message['answer'][0] if(isinstance(message['answer'],list)) else message['answer']}
                    }
                ]
            })
    return updated_gpt_vision_data
