# from dotenv import load_dotenv
# load_dotenv(".env.dev")

import base64,uuid,time,os,json,asyncio
from datetime import datetime
from streaming_form_data.targets import ValueTarget
from streaming_form_data import StreamingFormDataParser

from gen_ai_calling import gen_ai_calling_proxy

# from creating_page_wise_prompt_body import json_to_csv

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

    # used for the api gateway
    if (event.__contains__('path')):
        urlpath = event['path']

    headers = event['headers'] if (event.__contains__('headers')) else ""

    if ('body' in event.keys()):
        body = event['body']

    try:

        if (urlpath == "/generate"):

            reqobj = create_reqobj_scan(headers, body, "json")
            response = gen_ai_calling_proxy(reqobj)

        else:
            raise Exception("Unsupported path!")

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
            "body": json.dumps(response)
        }

    except Exception as e:
        
        status_code_value = 500
        status_message="Error in internal processing"
        return {  
            "statusCode": status_code_value,
            "headers": {"Content-Type": "application/json",
                        # "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
                        # Required for cookies, authorization headers with HTTPS
                        # "Access-Control-Allow-Credentials": True,
                        # "Access-Control-Allow-Headers": "*",
                        # "Access-Control-Allow-Methods": "*",  # Allow only GET request
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

        # parser = StreamingFormDataParser(headers=headers)

        # model_class_target = ValueTarget()
        # model_name_target = ValueTarget()
        # user_data_json_target = ValueTarget()
        
        # parser.register("modelClass", model_class_target)
        # parser.register("modelName", model_name_target)
        # parser.register("userDataJson",user_data_json_target)
        
        # # decode event body passed by the API
        # mydata = base64.b64decode(body)

        # # parse the decoded body based on registers defined above.
        # parser.data_received(mydata)

        # # covert binary value to UTF-8 format.
        # modelClass = model_class_target.value.decode("utf-8")
        # modelName = model_name_target.value.decode("utf-8")
        # userDataJson = user_data_json_target.decode("utf-8")
        
        # reqobj = {
        #     "modelClass": modelClass,
        #     "modelName": modelName,
        #     "userDataJson": json.loads(userDataJson)
        # }
        reqobj = json.loads(body)
    
    else:

        raise Exception("Invalid request type!")

    if ('scanId' not in reqobj or reqobj['scanId'] == ''):
        reqobj['scanId'] = str(uuid.uuid4())

    reqobj['receivedAt'] = datetime.utcnow().isoformat()

    return reqobj

if __name__ == "__main__":
    event = {}
    context = {}
    result = message_handler(event=event, context=context)
    if (os.environ['cloudWatch'] == "True"):
        print(result)
