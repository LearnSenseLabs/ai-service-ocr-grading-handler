# from dotenv import load_dotenv
# load_dotenv(".env.dev")

import uuid,os,json
from datetime import datetime

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
    # if (event.__contains__('requestContext')):
    #     if (event['requestContext'].__contains__('http')):
    #         urlpath = event['requestContext']['http']['path']

    # # used for the api gateway
    # if (event.__contains__('path')):
    #     urlpath = event['path']
    urlpath = "/generate"
    headers = event['headers'] if (event.__contains__('headers')) else ""
    
    # if ('body' in event.keys()):
    #     body = event['body']

    try:

        if (urlpath == "/generate"):

            reqobj = create_reqobj_scan(headers, event, "json")
            response = gen_ai_calling_proxy(reqobj)
            try:
                db_add_flag=add_response_to_db(response,reqobj)
                print(db_add_flag)
            except Exception as e:
                raise Exception("Error in adding response to DB!")
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
        reqobj_body = json.loads(body['Records'][0]['body'])
        if(isinstance(reqobj_body, list)):
            reqobj = reqobj_body[0]
        else:
            reqobj = reqobj_body
        # reqobj = json.loads(body['Records'][0]['body'])[0]
    
    else:

        raise Exception("Invalid request type!")

    if ('scanId' not in reqobj or reqobj['scanId'] == ''):
        reqobj['scanId'] = str(uuid.uuid4())

    reqobj['receivedAt'] = datetime.utcnow().isoformat()

    return reqobj

if __name__ == "__main__":
#     event = {
#     "Records": [
#         {
#             "messageId": "0041c27f-7433-4322-a74b-03923369a99f",
#             "receiptHandle": "AQEBwuxbncKqN3XsQ5SixYigiZSTJ8JAi7B87pt6CxKGyuNFaZKfSBVvczZhkM7AI/u8ZRbdzjK/peJyzu47PRkZtm1wrGPhN4b3DMXTITSygKOEyCneu6Ilp+dHPWMxBPfXKmE6FWZDaa4pC8uKG+BVO7Uc2L4O0B/vPzh/CLsN27yRMys9pPc9lSi66Iqf1TQLWWlQxGc29Rqcyqsuhe5sDcJksW0LNnvnZTCuHMBodpaYYh0mNYip0GMtCtEaNvLLRKFfznSVNHbqVqAPsFRbGO21Gsok19zmb89D3qrZ7GPfHCw7qzxSLjKnDGA8T3D0",
#             "body": "[{\"modelName\": \"gpt-4-latest\", \"questionInfo\": {\"question\": \"\", \"studentAnswer\": \"Some people say that people should continue to work after the retirement age. I agree with this statement because of health and money. First, It is health to walk for them. This is because walking makes them relax, for example, they can see a lot of beautiful nature when they can walk. Second, Walking means saving money. This is because we always want to have fun so we sometimes take a bus But sbases cost money. Therefore we should walk.\", \"rubrics\": [{\"rubricId\": \"9b8d81aa-aeab-47ca-afb7-3de9ec8a563b\", \"score\": 1, \"criteria\": \"Word Count (100+ / 120+ overall priority level will depend on whether Eiken 2 or pre-1)\"}, {\"rubricId\": \"e7e32279-486f-468d-8fa2-717d6d02dac6\", \"score\": 1, \"criteria\": \"Uses transition words or phrases to connect ideas\"}, {\"rubricId\": \"7ebf5d5c-85de-48ed-9ec9-81af6499b69c\", \"score\": 1, \"criteria\": \"clear opinion stated\"}, {\"rubricId\": \"c264a834-2c93-4eaa-8a0b-4b2ea3b7cf8b\", \"score\": 1, \"criteria\": \"supported with facts/reasons\"}, {\"rubricId\": \"d8ca99e7-f68b-4f6f-abf6-c53b9493d040\", \"score\": 1, \"criteria\": \"good vocabulary usage on topic (synonyms and antonyms, vocabulary from Monoxer)\"}, {\"rubricId\": \"f7837f0e-bb28-451d-a642-94e28d4b8621\", \"score\": 1, \"criteria\": \"uses subject sentence, transitions between topics, transitions between topics and conclusion effectively\"}, {\"rubricId\": \"a9670768-7dab-4aa0-80e8-4c5d3afce838\", \"score\": 1, \"criteria\": \"demonstrates correct use of an adverb (necessary at the pre-1 level)\"}, {\"rubricId\": \"aab94de0-eccb-4756-95a2-d448d22488c4\", \"score\": 1, \"criteria\": \"conclusion rephrases the main points made in body paragraph 1 and 2\"}], \"maxScore\": 8, \"studentAnswerUrl\": \"\"}, \"gradingPrompt\": \"essay\", \"studentId\": \"essay\", \"status\": \"processing\"}]",
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "SentTimestamp": "1723479785688",
#                 "SequenceNumber": "18887954898845679616",
#                 "MessageGroupId": "groupIdv1",
#                 "SenderId": "AIDA6KOFIGPVZCQQML6H3",
#                 "MessageDeduplicationId": "c593d3a6bc4ce9cc78e17a427d9126f4c0d9fd0e0e3b2cb424ccc33df6b28f5f",
#                 "ApproximateFirstReceiveTimestamp": "1723479785688"
#             },
#             "messageAttributes": {},
#             "md5OfBody": "05e69e8b7985320a16d2f45f5bb7c8bb",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:ap-south-1:984498058219:ai-serivce-llm-calling-queue.fifo",
#             "awsRegion": "ap-south-1"
#         }
#     ]
# }
    event = {}
    context = {}
    result = message_handler(event=event, context=context)
    if (os.environ['cloudWatch'] == "True"):
        print(result)
