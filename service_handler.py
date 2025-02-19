# from dotenv import load_dotenv
# load_dotenv(".env.dev")

from engine.core.llm_number_prediction import predict_llm_number
from engine.core.question_generation_handler import credit_reducer
import os,json

from engine.core.gen_ai_calling import gen_ai_calling_proxy
from engine.gen_utils_files.utils import add_response_to_db

generic_forbidden_response = {
    "statusCode": 403,
    "body": "Forbidden.",
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
        # Required for cookies, authorization headers with HTTPS
        "Access-Control-Allow-Credentials": True,
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "*",  # Allow only GET request
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }
}

def message_handler(event, context):

    # print(event)
    if (os.environ['cloudWatch'] == "True"):
        print(json.dumps(event))
    # print(context)
    if (event.__contains__('requestContext')):
        if (event['requestContext'].__contains__('http')):
            urlpath = event['requestContext']['http']['path']
        else:
            urlpath = "/generate"
    else:
        urlpath = "/generate"    

    # # used for the api gateway
    # if (event.__contains__('path')):
    #     urlpath = event['path']
    headers = event['headers'] if (event.__contains__('headers')) else ""
    
    # if ('body' in event.keys()):
    #     body = event['body']

    try:

        if (urlpath == "/generate"):

            reqobj = create_reqobj_scan(headers, event, "json")
            # print("reqobj, I got: ",reqobj)
            response = {}
            ensamble_list = []
            reqobj_task = ''
            ## added support for multiple questions in one request processing like adding loop to process questions one by one...
            for reqobj_question_wise in reqobj:
                # if(os.environ['cloudWatch'] == "True"):
                #     print(reqobj_question_wise)
                if(reqobj_question_wise['modelName']=='ensamble-vision'):
                    ensamble_list.append(reqobj_question_wise)
                    reqobj_task = 'number_llm_prediction'
                else:
                    response = gen_ai_calling_proxy(reqobj_question_wise)
                    if (os.environ['cloudWatch'] == "True"):
                        print("response: ",response)
                    try:
                        db_add_flag=add_response_to_db(response,reqobj_question_wise)
                        response_message = "question graded and database updated succesfully."
                        # if(os.environ['cloudWatch'] == "True"):
                        #     print("db_add_flag: ",db_add_flag," response_message: ",response_message)
                    except Exception as e:
                        raise Exception("Error in adding response to DB!")
            if(reqobj.__contains__('reqobj_task')):
               if(reqobj['reqobj_task']=='number_llm_prediction'):
                    response = predict_llm_number(reqobj)
                    # response=predict_llm_number(ensamble_list)
                    response_message = "question graded and database updated succesfully."
            # print(ensamble_list)
        elif(urlpath=="/generateQuestion"):
            reqobj_task = "question_generation"
            reqobj = create_reqobj_scan(headers, event, reqobj_task)
            reqobj_userId = reqobj[0]['userId']
            if(os.environ['cloudWatch'] == "True"):
                print(reqobj[0])
            response = gen_ai_calling_proxy(reqobj[0],task='question_generation')
            response_message = credit_reducer(reqobj_userId,response)
            # response_message = "question generated successfully."
        elif(urlpath=="/latexToImage"):
            reqobj_task = "latex_to_image"
            reqobj = create_reqobj_scan(headers, event, reqobj_task)
            if(os.environ['cloudWatch'] == "True"):
                print(reqobj[0])
            response = gen_ai_calling_proxy(reqobj,task=reqobj_task)
        elif(urlpath=="/asciiMathToImage"):
            reqobj_task = "ascii_to_image"
            reqobj = create_reqobj_scan(headers, event, reqobj_task)
            if(os.environ['cloudWatch'] == "True"):
                print(reqobj[0])
            response = gen_ai_calling_proxy(reqobj,task=reqobj_task)
        else:
            raise Exception("Unsupported path!")
        
        if(reqobj_task=='question_generation'):
            return {
                "statusCode": 200 if isinstance(response, list) else response['statusCode'],
                "headers": {
                    "Content-Type": "application/json",
                    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
                },
                "body": json.dumps({"feedback":response_message,"status":True,"generated_questions":response})
            }
        elif(reqobj_task=='latex_to_image' or reqobj_task=='ascii_to_image'):
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
                },
                "body": json.dumps({"response":response})
            }
        else:
            return {
                "statusCode": 200 if isinstance(response, list) else response['statusCode'],
                "headers": {"Content-Type": "application/json",
                            # "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
                            # Required for cookies, authorization headers with HTTPS
                            # "Access-Control-Allow-Credentials": True,
                            # "Access-Control-Allow-Headers": "*",
                            # "Access-Control-Allow-Methods": "*",  # Allow only GET request
                            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
                            },
                "body": json.dumps({"feedback":response_message})
            }

    except Exception as e:
        
        status_code_value = 500
        status_message="Error in internal processing"
        return {  
            "statusCode": status_code_value,

            "headers": {"Content-Type": "application/json",
                        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
                        },
            "body": json.dumps({
                "status": status_message,
                "errorMessage": str(e)
            })
        }


def create_reqobj_scan(headers, body, reqtype):

    def as_bool(x):

        if (x == ''):
            return ''

        if (x == "1" or x == "true" or x == "True" or x == "t" or x == "T"):
            return True
        else:
            return False

    if (reqtype == "json"):
        reqobj_body = json.loads(body['Records'][0]['body'])
        
        ## to accoumulate multiple questions in one request
        
        # reqobj = json.loads(body['Records'][0]['body'])[0]
    elif(reqtype=="question_generation" or reqtype=="latex_to_image" or reqtype=="ascii_to_image"):
        reqobj_body = json.loads(body['body'])
    else:
        raise Exception("Invalid request type!")

    # if ('scanId' not in reqobj or reqobj['scanId'] == ''):
    #     reqobj['scanId'] = str(uuid.uuid4())
    if(isinstance(reqobj_body, list)):
        reqobj = reqobj_body
    else:
        reqobj = [reqobj_body]
    # reqobj['receivedAt'] = datetime.utcnow().isoformat()

    return reqobj

if __name__ == "__main__":
 
    event = {}

    context = {}
    result = message_handler(event=event, context=context)
    if (os.environ['cloudWatch'] == "True"):
        print(result)