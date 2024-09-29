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
            # print("reqobj: ",reqobj)
            
            ## added support for multiple questions in one request processing like adding loop to process questions one by one...
            for reqobj_question_wise in reqobj:
                response = gen_ai_calling_proxy(reqobj_question_wise)
                # print("response: ",response)
                try:
                    db_add_flag=add_response_to_db(response,reqobj_question_wise)
                    # print("db_add_flag: ",db_add_flag)
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
            "body": json.dumps({"feedback":"question graded and database updated succesfully."})
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
        if(isinstance(reqobj_body, list)):
            reqobj = reqobj_body
        else:
            reqobj = [reqobj_body]
        # reqobj = json.loads(body['Records'][0]['body'])[0]
    
    else:

        raise Exception("Invalid request type!")

    # if ('scanId' not in reqobj or reqobj['scanId'] == ''):
    #     reqobj['scanId'] = str(uuid.uuid4())

    # reqobj['receivedAt'] = datetime.utcnow().isoformat()

    return reqobj

if __name__ == "__main__":
#     event = {
#     "Records": [
#         {
#             "messageId": "0041c27f-7433-4322-a74b-03923369a99f",
#             "receiptHandle": "AQEBwuxbncKqN3XsQ5SixYigiZSTJ8JAi7B87pt6CxKGyuNFaZKfSBVvczZhkM7AI/u8ZRbdzjK/peJyzu47PRkZtm1wrGPhN4b3DMXTITSygKOEyCneu6Ilp+dHPWMxBPfXKmE6FWZDaa4pC8uKG+BVO7Uc2L4O0B/vPzh/CLsN27yRMys9pPc9lSi66Iqf1TQLWWlQxGc29Rqcyqsuhe5sDcJksW0LNnvnZTCuHMBodpaYYh0mNYip0GMtCtEaNvLLRKFfznSVNHbqVqAPsFRbGO21Gsok19zmb89D3qrZ7GPfHCw7qzxSLjKnDGA8T3D0",
#             "body": "[{\"modelName\": \"shozemi-gpt-latest\", \"questionInfo\": {\"question\": \"\", \"studentAnswer\": \"Some people say that people should continue to work after the retirement age. I agree with this statement because of health and money. First, It is health to walk for them. This is because walking makes them relax, for example, they can see a lot of beautiful nature when they can walk. Second, Walking means saving money. This is because we always want to have fun so we sometimes take a bus But sbases cost money. Therefore we should walk.\", \"rubrics\": [{\"rubricId\": \"9b8d81aa-aeab-47ca-afb7-3de9ec8a563b\", \"score\": 1, \"criteria\": \"Word Count (100+ / 120+ overall priority level will depend on whether Eiken 2 or pre-1)\"}, {\"rubricId\": \"e7e32279-486f-468d-8fa2-717d6d02dac6\", \"score\": 1, \"criteria\": \"Uses transition words or phrases to connect ideas\"}, {\"rubricId\": \"7ebf5d5c-85de-48ed-9ec9-81af6499b69c\", \"score\": 1, \"criteria\": \"clear opinion stated\"}, {\"rubricId\": \"c264a834-2c93-4eaa-8a0b-4b2ea3b7cf8b\", \"score\": 1, \"criteria\": \"supported with facts/reasons\"}, {\"rubricId\": \"d8ca99e7-f68b-4f6f-abf6-c53b9493d040\", \"score\": 1, \"criteria\": \"good vocabulary usage on topic (synonyms and antonyms, vocabulary from Monoxer)\"}, {\"rubricId\": \"f7837f0e-bb28-451d-a642-94e28d4b8621\", \"score\": 1, \"criteria\": \"uses subject sentence, transitions between topics, transitions between topics and conclusion effectively\"}, {\"rubricId\": \"a9670768-7dab-4aa0-80e8-4c5d3afce838\", \"score\": 1, \"criteria\": \"demonstrates correct use of an adverb (necessary at the pre-1 level)\"}, {\"rubricId\": \"aab94de0-eccb-4756-95a2-d448d22488c4\", \"score\": 1, \"criteria\": \"conclusion rephrases the main points made in body paragraph 1 and 2\"}], \"maxScore\": 8, \"studentAnswerUrl\": \"\"}, \"gradingPrompt\": \"shozemi-ocr\", \"studentId\": \"essay\", \"status\": \"processing\"}]",
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
#     event = {
#     "Records": [
#         {
#             "messageId": "b1cec3ac-b5f2-458b-a9e5-f617b094fda6",
#             "receiptHandle": "AQEB/2T7ra5hJ1H/v6e8zMkDI3BSQv/J0uH8dQt7bOZTebXXFpIjwD7LoMImBbNiISWSD8OG5X02otrJLg7A3DxYtJk4rEf2UmPbF4wn/Dz41K2iqlQ48prEOPZBFhI3T+6OTntl0e07bwa0v/iBOKHMZ6kYMlMAr6NkrYQcSPkY2Pg3rf+tb7i2Vz0Q0VfIfkN7GIViOnthV8ejZl/naV+gLRRnTEXhxZzL8Kjov8EjFMiOg/8XR8w36S9Z+kvUSTW57oaJRZFV17QByLRW5v/+0gbnR1vHFq7ZNrC2RIC5ib8ca+P+Nr4pLUUZo3FjXdTDa4MJhqLKIjvwAnl8fM/vEjVED1GdSSNK8J6B6ke7OX1XmoysGNUXpENR2NPDxnu/I70YUi4cRCI8DLMO0kagjn6oTIuKkRK2QpLeKZTgpXg=",
#             "body": "[{\"modelName\": \"shozemi-gpt-latest\", \"questionInfo\": {\"question\": \"Solve for y: 4y + 5 = 21\", \"studentAnswer\": \"44+6 = 21 4 4 = 21-5 44: 20 y = 5\", \"rubrics\": [{\"rubricId\": \"f63de483-5b44-4892-9cdc-0996fc1e3b2a\", \"score\": 1, \"criteria\": \"Correctly isolating the term 4y by subtracting 5 from both sides.\"}, {\"rubricId\": \"f391ffa8-c28f-4440-b24d-8906a09411c7\", \"score\": 1, \"criteria\": \"Correctly solving for y to get y = 4\"}], \"maxScore\": 2, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/66e53d08feff562691036a58/c75366f0-f62c-4e98-807b-a4ed77bc4ea5/ans_crop/bb665f64-7717-4e1c-a950-5af6fee50a4c.webp\"}, \"gradingPrompt\": \"ocr\", \"status\": \"processing\", \"scanId\": \"c75366f0-f62c-4e98-807b-a4ed77bc4ea5\", \"studentId\": \"eSQgTQAGSzZtLTepQu40T\", \"queId\": \"f0c0d293-332e-4b60-be4a-e4969ef71da1\"}, {\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"The sum of a number and its double is 18. Find the number.\", \"studentAnswer\": \"n + 2n = 18 3 n= 18 n= 6\", \"rubrics\": [{\"rubricId\": \"6c1d8148-a95e-49f2-bd6a-5efc7066f4da\", \"score\": 1, \"criteria\": \"Setting up the correct equation n + 2n = 18 or 3n = 18\"}, {\"rubricId\": \"f23461e3-7476-4ae3-bdbd-f88a5334ea7e\", \"score\": 1, \"criteria\": \"Correctly solving for n to get n = 6\"}], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/66e53d08feff562691036a58/c75366f0-f62c-4e98-807b-a4ed77bc4ea5/ans_crop/55309f6c-e69f-41ee-b006-0fe6e28bd527.webp\"}, \"gradingPrompt\": \"ocr\", \"status\": \"processing\", \"scanId\": \"c75366f0-f62c-4e98-807b-a4ed77bc4ea5\", \"studentId\": \"eSQgTQAGSzZtLTepQu40T\", \"queId\": \"421dce28-a434-4599-afbb-3605270cf42e\"}]",
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "SentTimestamp": "1727318677687",
#                 "SenderId": "AIDA6KOFIGPVZCQQML6H3",
#                 "ApproximateFirstReceiveTimestamp": "1727318677691"
#             },
#             "messageAttributes": {},
#             "md5OfBody": "1b217d22ae6145d8d78def62dcd43280",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:ap-south-1:984498058219:ai-serivce-llm-calling-queue-prod",
#             "awsRegion": "ap-south-1"
#         }
#     ]
# }

    event = {}
    context = {}
    result = message_handler(event=event, context=context)
    if (os.environ['cloudWatch'] == "True"):
        print(result)
