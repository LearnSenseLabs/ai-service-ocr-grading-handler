# from dotenv import load_dotenv
# load_dotenv(".env.dev")

import uuid,os,json
# from datetime import datetime

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
            response = {}
            ## added support for multiple questions in one request processing like adding loop to process questions one by one...
            for reqobj_question_wise in reqobj:
                if(os.environ['cloudWatch'] == "True"):
                    print(reqobj_question_wise)
                response = gen_ai_calling_proxy(reqobj_question_wise)
                if (os.environ['cloudWatch'] == "True"):
                    print("response: ",response)
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
#             "messageId": "e0598b01-5a55-452e-a651-29a5e689942d",
#             "receiptHandle": "AQEBUSYQnljzswnOKQh/xwgzqiL0aworvCzshO/oJTFqpXkWZXTdNd6g39ZNsrdYgtEIOxRAOvWhhrSOkQKSyrQaHDBaPOrbzcEd31Hu6sN/vmA8JNTNBclm166xWCxiHmhD+9QIp6kVoGBughN0b/mHo3ncYvYGWgfey/uJXV0QUXIiN/cKveToilxMOyz+CeKlt+fhT5OIyFqenwVbJjmK+2urHDDnftPB3TIPxxBXZ5Z32vaz58cYTnpFB4EsNxrfdXpCTZ+RqvkBEKdp4JySXchJwDmvZHnyFYV53CnLHx4ERvIOAsUiBMlo3umFlnO2Pk+jN7/WKOxlrnzKBDj8f53CeL/RDR3l+Qx2ixyY4Eqtu2gsSCoY7o3uT66DWOBc96NToNQm5n5FiLl51flkG/5oi6Y1/jbaQ+pXupM38tI=",
#             "body": "[{\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"Measure the angles of a triangle that has sides of lengths 3 cm, 4 cm, and 5 cm.\", \"studentAnswer\": \"\\\"The triangles with lengths - 3cm, 4cm & 5cm\\n\\nThe triangle satisfies 3\\u00b2 + 4\\u00b2 = 25 = 5\\u00b2 \\u2192 Pythagorean theorem.\\n\\nThe first angle is will be 90\\u00b0 which is opposite to the length 5cm.\\n\\nAngle opp. to 3cm \\u21d2 sin\\u03b8 = opp. = 3 \\u2234 \\u03b8 = 36.87\\u00b0\\n                        hypo.   5\\n\\nNow as \\u03b8 = 36.87\\u00b0 & 90\\u00b0 \\u2234\\nlast angle = 180 - 36.87 - 90\\u00b0 = 53.13\\u00b0\\\"\", \"rubrics\": [{\"rubricId\": \"c960c744-c873-4e31-bbd5-e62fc272cb68\", \"score\": 1, \"criteria\": \"Correctly identifies that the triangle is a right-angled triangle (since 3\\u00b2 + 4\\u00b2 = 5\\u00b2, satisfying the Pythagorean theorem).\"}, {\"rubricId\": \"42ad5339-f7c2-4c84-80b3-1ae5c6ba3122\", \"score\": 1, \"criteria\": \"Correctly determines that the right angle is opposite the side of length 5 cm (i.e., 90\\u00b0).\"}, {\"rubricId\": \"baffa790-b9af-421c-bd04-4c5eda5fa111\", \"score\": 1, \"criteria\": \"Correctly calculates the angle opposite the side of length 3 cm as 36.87\\u00b0 using trigonometric functions (or sine/cosine rule).\"}, {\"rubricId\": \"a8ca8dcf-ad7e-404f-97e9-c22c032ad17c\", \"score\": 1, \"criteria\": \"Correctly calculates the angle opposite the side of length 4 cm as 53.13\\u00b0 (since the sum of angles in a triangle is 180\\u00b0).\"}], \"maxScore\": 4, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/master/67038612fe605db1a332ba7a/xOqh6vPeXLGF3qMQhWLTg/ans_crop/ec0dbff0-2f0e-45ea-8705-aed8b9330084.webp\"}, \"gradingPrompt\": \"claude-ocr\", \"status\": \"processing\", \"student_id\": \"IfoHF2t1eZW4Z22UQD8eY\", \"scan_id\": \"xOqh6vPeXLGF3qMQhWLTg\", \"que_id\": \"5ca22a6c-dfe8-410c-b4eb-911393b73391\"}]",
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "AWSTraceHeader": "Root=1-670651f9-1de5c67d67d46ca431286874;Parent=4d055eebb5faad7c;Sampled=0;Lineage=1:bd4cecd5:0",
#                 "SentTimestamp": "1728467452252",
#                 "SenderId": "AIDA6KOFIGPVZCQQML6H3",
#                 "ApproximateFirstReceiveTimestamp": "1728467452257"
#             },
#             "messageAttributes": {},
#             "md5OfBody": "63857ac104629a58015f81eb7311b241",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:ap-south-1:984498058219:ai-serivce-llm-calling-queue-prod-new",
#             "awsRegion": "ap-south-1"
#         }
#     ]
# }

    event = {}
    context = {}
    result = message_handler(event=event, context=context)
    if (os.environ['cloudWatch'] == "True"):
        print(result)
    ## last deployment: 984498058219.dkr.ecr.ap-south-1.amazonaws.com/gen_ai_proxy_dev@sha256:d640348ca746b0a0372fd32a7037890a6bb913f83b3f6be6bd6e2ea67590463a