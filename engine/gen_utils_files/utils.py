import base64
import json,re,os,boto3
import uuid
import httpx

sqs = boto3.resource('sqs',
                     aws_access_key_id=os.environ['USER_ACCESS_KEY_ID'],
                     aws_secret_access_key=os.environ['USER_SECRET_ACCESS_KEY'],
                     region_name="ap-south-1"
                     )
s3 = boto3.client('s3',
                  aws_access_key_id=os.environ['USER_ACCESS_KEY_ID'],
                  aws_secret_access_key=os.environ['USER_SECRET_ACCESS_KEY'],
                  region_name="ap-south-1")

def field_exist_or_not(user_response,default_response,field_to_check):
    if(user_response['response'].__contains__(field_to_check)):
        requested_field_data = user_response['response'][field_to_check] if (user_response['response'][field_to_check]!="") else default_response
    else:
        requested_field_data = default_response
    return requested_field_data

def get_prompt(task, subject_name, prompts_json_data):
    
    for prompt in prompts_json_data:
        if prompt["task"] == task and prompt["subjectName"].lower() == subject_name.lower():
            return prompt["promptText"]
    
    return "You will read the handwritting in the given image, write what you read in the image as it is, "

# def load_prompts(file_path):
#     with open(file_path, 'r') as file:
#         prompts_list = json.load(file)
    
#     # Create a lookup dictionary using (task, subjectName) as key
#     prompts_dict = {
#         (prompt["task"], prompt["subjectName"].lower()): prompt["promptText"]
#         for prompt in prompts_list
#     }
    
#     return prompts_dict

# def get_prompt(task, subject_name, prompts_dict):
#     return prompts_dict.get((task, subject_name.lower()), "No prompt found for the given task and subject name.")

def json_s3_uploads(user_id, json_data):

    res_url = []
    s3_bucket_name = 'open-crops-smartpaper'
    # overriding file name
    file_name = str(uuid.uuid4())

    file_name = str(file_name)
    content_type = 'application/json'
    s3_key = 'dev'+ "/" + user_id + "/" + file_name +".json"
    response = s3.put_object(Body=json_data,Bucket=s3_bucket_name, Key=s3_key, ACL='public-read', ContentType=content_type)

    s3_url = "https://"+s3_bucket_name+".s3.ap-south-1.amazonaws.com/"+s3_key
    # res_url.append(s3_url)
    return s3_url

def convert_to_add_data_format(user_id,question_json):
    response = []
    response.append({
        "user_id":user_id,
        "question_json_url":json_s3_uploads(user_id,question_json),
        "usage":"insertData"
    })
    return response

def add_response_to_db(user_response,reqobj,task=''):
    ai_service_db_update_queue = sqs.get_queue_by_name(QueueName=os.environ['AI_SERVICE_DB_UPDATE_QUEUE'])

    if(task=="question_generation"):
        response_to_add_in_queue=convert_to_add_data_format(user_id=reqobj['userId'],question_json=json.dumps(user_response))
        response_flag = ai_service_db_update_queue.send_message(MessageBody=json.dumps(response_to_add_in_queue))
        return response_flag
    
    ## add test case for checking studentId,scanId,queId exist or not.
    student_id = reqobj['studentId'] if (reqobj.__contains__('studentId')) else reqobj['student_id'] if(reqobj.__contains__('student_id')) else ''
    
    scan_id = reqobj['scanId'] if (reqobj.__contains__('scanId')) else reqobj['scan_id'] if(reqobj.__contains__('scan_id')) else ''
    
    que_id = reqobj['queId'] if (reqobj.__contains__('queId')) else reqobj['que_id'] if(reqobj.__contains__('que_id')) else ''
    
    ## checking and assigning the values from ai response to the variables
    student_answer_ocr = field_exist_or_not(user_response,reqobj['questionInfo']['studentAnswer'],'ocr')
    student_answer_maxScore = field_exist_or_not(user_response,1,'maxScore')
    student_answer_score = field_exist_or_not(user_response,0,'score')
    student_answer_aiFeedback = field_exist_or_not(user_response,'','aiFeedback')
    if(student_answer_aiFeedback==''):
        student_answer_aiFeedback = field_exist_or_not(user_response,'','feedback')
    
    ## desciding the flags value based on the score and maxScore
    if(student_answer_score==student_answer_maxScore):
        student_answer_correct_flag = True
    elif(student_answer_score<student_answer_maxScore and student_answer_score>0):
        student_answer_correct_flag = False
    else:
        student_answer_correct_flag = False
    
    if(isinstance(student_answer_ocr,int)):
        if(student_answer_ocr==''):
            student_answer_empty_flag = True
        else:
            student_answer_empty_flag = False
    else:    
        if(student_answer_ocr=='' or student_answer_ocr.lower()=='Empty Response'):
            student_answer_empty_flag = True
        else:
            student_answer_empty_flag = False
            
    ## creating data to send to queue
    reqobj_to_update = {
        'key_value_pair_to_update_data':{'aiFeedback':student_answer_aiFeedback,
                                'score':student_answer_score,
                                'studentAnswer':student_answer_ocr,
                                'isCorrect':student_answer_correct_flag,
                                'isBlank':student_answer_empty_flag,
                                'status':'processed',
                                },
        'key_value_pair_to_filter_data':{'studentId':student_id,'scanId':scan_id,'queId':que_id},
        'usage':'updateData'
    }
    # print("reqobj to update data: ",json.dumps(reqobj_to_update))
    # sending the data to queue
    response_flag = ai_service_db_update_queue.send_message(MessageBody=json.dumps(reqobj_to_update))

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
    score_level_based = 0
    for feedback in feedback_list:
        formatted_feedback += f"{ feedback['FeedbackPointName']} - {feedback['improvement']}\n\n"
        level_name = feedback['levelName']
        if level_name is not None:
            if(level_name=='Effective' or level_name=='Good' or level_name=='Satisfactory'):
                score_level_based+=1
            elif(level_name=='Normal' or level_name=='Fair'):
                score_level_based+=0.5
            else:
                score_level_based+=0
        # formatted_feedback += f"level name - {feedback['levelName']}\n"
    
    return formatted_feedback.strip(),score_level_based

def encode_image(image_url):
    return base64.b64encode(httpx.get(image_url).content).decode("utf-8")

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
        if(matches_json!=None):
            return matches_json.group(0) if len(matches_json.group()) > 0 else data_string
        else:
            return data_string
    elif(type=="argumentative-essay-ocr"):
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
