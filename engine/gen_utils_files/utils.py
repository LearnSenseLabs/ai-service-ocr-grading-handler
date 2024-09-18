import json,re,os,boto3

sqs = boto3.resource('sqs',
                     aws_access_key_id=os.environ['USER_ACCESS_KEY_ID'],
                     aws_secret_access_key=os.environ['USER_SECRET_ACCESS_KEY'],
                     region_name="ap-south-1"
                     )

def add_response_to_db(user_response,reqobj):
    ai_service_db_update_queue = sqs.get_queue_by_name(QueueName=os.environ['AI_SERVICE_DB_UPDATE_QUEUE'])
    
    ## add test case for checking studentId,scanId,queId exist or not.
    student_id = reqobj['studentId'] if (reqobj.__contains__('studentId')) else ''
    
    scan_id = reqobj['scanId'] if (reqobj.__contains__('scanId')) else ''
    
    que_id = reqobj['queId'] if (reqobj.__contains__('queId')) else ''
    
    if(user_response['response'].__contains__('ocr')):
        student_answer_ocr = user_response['response']['ocr'] if (user_response['response']['ocr']!="") else reqobj['questionInfo']['studentAnswer']
    else:
        student_answer_ocr = reqobj['questionInfo']['studentAnswer']
    
    reqobj_to_update = {
        'key_value_pair_to_update_data':{'aiFeedback':user_response['response']['aiFeedback'],
                                'score':user_response['response']['score'],
                                'studentAnswer':student_answer_ocr,
                                'status':'processed',
                                },
        'key_value_pair_to_filter_data':{'studentId':student_id,'scanId':scan_id,'queId':que_id},
        'usage':'updateData'
    }
    
    response_flag = ai_service_db_update_queue.send_message(MessageBody=json.dumps(reqobj_to_update))
    # print("update is deployed...")
    return response_flag

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
        data_string_clean = re.sub(r'^"+|"+$', '', data_string)
        # Regex pattern for ocr:"value" and ocr:'value'
        pattern_ocr = r"(?i)ocr:\s*['\"](.*?)['\"]"

        # Regex pattern for JSON { "ocr": "value" }
        pattern_json = r"(?i)\{\s*['\"]ocr['\"]\s*:\s*['\"](.*?)['\"]\s*\}"

        # Find all matches for both patterns
        matches_ocr = re.findall(pattern_ocr, data_string_clean)
        matches_json = re.findall(pattern_json, data_string_clean)

        # Combine the results
        matches = matches_ocr + matches_json
        return matches[0] if len(matches) > 0 else data_string_clean
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
