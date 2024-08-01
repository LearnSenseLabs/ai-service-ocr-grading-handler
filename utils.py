import json,re
def convert_rubric_to_string(rubric_json):
    if(isinstance(rubric_json,list)):
        rubric_string = "Rubrics: "
        for rubrics_json_data in rubric_json:
            rubric_string+=(str(rubrics_json_data['score'])+" Points: ")+(rubrics_json_data['criteria']+", ")
            # print(rubrics_json_data)
        return rubric_string
    else:
        return rubric_json
def mapping_model_with_name(model_name,llm_name_mapping):
    for key,value in llm_name_mapping.items():
        if(key==model_name):
            return value
    return "model does not found"
def convert_feedback_format(feedback_json):
    feedback_list = json.loads(feedback_json)
    formatted_feedback = ""
    
    for feedback in feedback_list:
        formatted_feedback += f"{feedback['FeedbackPointName']} - {feedback['improvement']}\n"
        # formatted_feedback += f"level name - {feedback['levelName']}\n"
    
    return formatted_feedback.strip()

def find_data_in_string(data_string,type="ocr"):
    if(type=="ocr"):

        # Regex pattern for ocr:"value" and ocr:'value'
        pattern_ocr = r"(?i)ocr:\s*['\"](.*?)['\"]"

        # Regex pattern for JSON { "ocr": "value" }
        pattern_json = r"(?i)\{\s*['\"]ocr['\"]\s*:\s*['\"](.*?)['\"]\s*\}"

        # Find all matches for both patterns
        matches_ocr = re.findall(pattern_ocr, data_string)
        matches_json = re.findall(pattern_json, data_string)

        # Combine the results
        matches = matches_ocr + matches_json
        return matches[0] if len(matches) > 0 else data_string
    elif(type=="claude-json"):
        pattern_json = re.compile(r'\{.*?\}', re.DOTALL)
        matches_json=pattern_json.search(data_string)
        return matches_json.group(0) if len(matches_json.group()) > 0 else data_string
    elif(type=="shozemi-gpt-vision"):
        pattern_json = re.compile(r'\{.*?\}', re.DOTALL)
        matches_json = pattern_json.findall(data_string)
        
        # Convert each JSON string to a Python dictionary
        json_objects = [json.loads(match) for match in matches_json]
        
        # Combine all dictionaries into a list
        combined_json = json_objects
        
        # Convert the list of dictionaries to a JSON array string
        final_json_string = json.dumps(combined_json, indent=4)
        final_string = convert_feedback_format(final_json_string)
        return final_string
