# from dotenv import load_dotenv
# load_dotenv(".env.dev")

from engine.core.question_generation_handler import credit_reducer
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
            # print("reqobj: ",reqobj)
            response = {}
            reqobj_task = ''
            ## added support for multiple questions in one request processing like adding loop to process questions one by one...
            for reqobj_question_wise in reqobj:
                if(os.environ['cloudWatch'] == "True"):
                    print(reqobj_question_wise)
                response = gen_ai_calling_proxy(reqobj_question_wise)
                if (os.environ['cloudWatch'] == "True"):
                    print("response: ",response)
                try:
                    db_add_flag=add_response_to_db(response,reqobj_question_wise)
                    response_message = "question graded and database updated succesfully."
                except Exception as e:
                    raise Exception("Error in adding response to DB!")
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
        elif(reqobj_task=='latex_to_image'):
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
    elif(reqtype=="question_generation" or reqtype=="latex_to_image"):
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

#     event = {
#     "Records": [
#         {
#             "messageId": "5415cd1d-6a58-44ff-be2b-6358327a9259",
#             "receiptHandle": "AQEBWIYAAmYBPJlBZVmldxZ7ZG9h0Or97FnmPApbJpSu08jb8B8xYyWmZANdWVrIR6les3v6vNJGc3F62toUpSYRDLt7qr1ehC3zX6VEKp14aNz4SjBKmXo4kPCEodJDg2GfmCbszJOg5JVGm7Tmee9REPQs7AbwYj9pUX+FTJS3LVKFB8yNOtyFPDQTzrrnZzRuHw/Gnrss8YpsU80aU8KdwmG+Ifo6vFkEv18U9pGqxIGNtChLSF1ccaL4+wtMNY2HDnoFgUPbwdd/O75RkdlCdBZDIBlnSRwaCFVysX2FXQfGfM4Qwv6l4lj3uOG487hvc/v+qXGLJy+9WfDS+i09bEuohyVClkvCaLSSlByqbQOL23F7Zua28cB7tV1pOrXhIvLyePNVltMmiamT188hLDI+Q3JGgpt7Z5y2ZNdEpjo=",
#             "body": "[{\"modelName\": \"claude-vision-ocr\", \"subject\": \"Mathematics\", \"retryFlag\": \"both\", \"questionInfo\": {\"question\": \"Simplify the expression: (3x + 4)(2x - 5)/(x\\u00b2 - 9)\", \"studentAnswer\": \"{6x^2 - 7x - 20}\", \"rubrics\": [{\"rubricId\": \"L0Bkg3bdyucbZCmDspQyy\", \"score\": 1, \"criteria\": \"1 mark for correctly identifying or factoring x\\u00b2 - 9 as a difference of squares: x\\u00b2 - 9 = (x+3)(x-3)\"}, {\"rubricId\": \"73c3eaa8-6936-4f24-af60-b31559fa6cad\", \"score\": 1, \"criteria\": \"1 mark for correctly expanding the product of the two binomials (3\\ud835\\udc65+4)(2\\ud835\\udc65\\u22125) using the distributive property (FOIL): (3\\ud835\\udc65+4)(2\\ud835\\udc65\\u22125)  = 6x\\u00b2 -15\\ud835\\udc65 +8\\ud835\\udc65 -20 = 6x\\u00b2  - 7\\ud835\\udc65 -20\"}, {\"rubricId\": \"71dbc04d-2c40-409d-b51d-a7366e30ac35\", \"score\": 1, \"criteria\": \"1 mark for dividing the expanded expression (6x\\u00b2  - 7\\ud835\\udc65 -20) with the factored form (x+3)(x-3) and simplifying: (6x\\u00b2  - 7\\ud835\\udc65 -20)/((x+3)(x-3))\"}], \"maxScore\": 3, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/master/67067d2a62458895dc7bc820/N7rQKHDS8H3Hi8dcPyCNH/ans_crop/df0194a7-f3f1-4e25-bacf-03b8c53aa89a.webp\"}, \"gradingPrompt\": \"claude-ocr\", \"status\": \"processing\", \"student_id\": \"WyYdZ1hcGf0moeMpA2Kqm\", \"scan_id\": \"N7rQKHDS8H3Hi8dcPyCNH\", \"que_id\": \"wapb-n7DgS_caZ2zv3lDK\"}]",
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "AWSTraceHeader": "Root=1-6711edf3-2ee6e6c463011266604c3b43;Parent=3c5daa0344327c88;Sampled=0;Lineage=1:bd4cecd5:0",
#                 "SentTimestamp": "1729228276043",
#                 "SenderId": "AIDA6KOFIGPVZCQQML6H3",
#                 "ApproximateFirstReceiveTimestamp": "1729228276048"
#             },
#             "messageAttributes": {},
#             "md5OfBody": "995d2c9d536320e1de0c99a96bd36cd1",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:ap-south-1:984498058219:ai-serivce-llm-calling-queue-prod-new",
#             "awsRegion": "ap-south-1"
#         }
#     ]
# }

#     event = {
#     "Records": [
#         {
#             "messageId": "eb04aca5-f29f-4e86-aee8-7d052038aff1",
#             "receiptHandle": "AQEBnXab0ab/b9JsrFvvX/HQELDTIaP2VqMx9y2opzHF5ZQdW48uJE9CaYvWwjJLMLY+mlBl1cLQni/knWNz61UdeG4+LMA3bfI7STRIzOUI6TJGNsrVmIUNY6rDFsSfyvEWrFQgjvxpYFZNLWoqqtY4aNpX2zFZjJxOXO8gSRLAl91AKM6aO9KsUAHQ76SUtcvIxP+IzgdS1dNvnmM6TJhnjDokbHvwHXkTLuHD8xXDCR76rftY3joms0rI7QgDFF6O6vKwFN6EuYB4MQrD/okZpbUhpkk07MYd10SAi8nvneu0wagpyuZBCY/ejLd8Db02KpJkuJM08Gxbdw87/dn8uihcnbFb3ktiCwtpE2YzlsqscjUDglUt8nnk8CMkjWNEjDxFia/sK+Af4JP6DThpa5wAPoTrdUSnFpayUa+7lWA=",
#             "body": "{\"gradeLevel\": \"grade1\", \"subject\": \"Mathematics\", \"educationBoard\": \"ICSE\", \"topic\": \"addition\", \"numberOfQuestions\": 5, \"userId\": \"66d176665d3a75527a7a161e\", \"contentType\": [\"mcq\", \"openEnded\"], \"task\": \"question_generation\"}",
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "AWSTraceHeader": "Root=1-67167bd7-7d9ecdf7202d31d70faa2a4d;Parent=5e079745d0b540ce;Sampled=0;Lineage=1:b8702b44:0",
#                 "SentTimestamp": "1729526745509",
#                 "SenderId": "AIDA6KOFIGPVZCQQML6H3",
#                 "ApproximateFirstReceiveTimestamp": "1729526745514"
#             },
#             "messageAttributes": {},
#             "md5OfBody": "f7261b111da7a2a27f610a34b91fa453",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:ap-south-1:984498058219:ai-serivce-llm-calling-queue-prod-new",
#             "awsRegion": "ap-south-1"
#         }
#     ]
# }


    # event = {'version': '2.0', 'routeKey': '$default', 'rawPath': '/generate', 'rawQueryString': '', 'headers': {'content-length': '248', 'x-amzn-tls-version': 'TLSv1.3', 'x-forwarded-proto': 'https', 'postman-token': 'b75d5d36-8cbc-4d41-8206-a012f1898701', 'x-forwarded-port': '443', 'x-forwarded-for': '43.241.194.3', 'accept': '*/*', 'x-amzn-tls-cipher-suite': 'TLS_AES_128_GCM_SHA256', 'x-amzn-trace-id': 'Root=1-67176cb2-1e55a5824575d3c109a08ae3', 'host': '4bf5c7dxjn3e3e6wrgxbypjexu0acnjw.lambda-url.ap-south-1.on.aws', 'content-type': 'application/json', 'cache-control': 'no-cache', 'accept-encoding': 'gzip, deflate, br', 'user-agent': 'PostmanRuntime/7.37.3'}, 'requestContext': {'accountId': 'anonymous', 'apiId': '4bf5c7dxjn3e3e6wrgxbypjexu0acnjw', 'domainName': '4bf5c7dxjn3e3e6wrgxbypjexu0acnjw.lambda-url.ap-south-1.on.aws', 'domainPrefix': '4bf5c7dxjn3e3e6wrgxbypjexu0acnjw', 'http': {'method': 'POST', 'path': '/generateQuestion', 'protocol': 'HTTP/1.1', 'sourceIp': '43.241.194.3', 'userAgent': 'PostmanRuntime/7.37.3'}, 'requestId': '62598eee-43ee-4780-b27a-2b2933192a0a', 'routeKey': '$default', 'stage': '$default', 'time': '22/Oct/2024:09:13:22 +0000', 'timeEpoch': 1729588402257}, 'body': '{\n    "gradeLevel": "grade6",\n    "subject": "Mathematics",\n    "educationBoard": "ICSE",\n    "topic": "addition",\n    "numberOfQuestions": 5,\n    "userId": "66d176665d3a75527a7a161e",\n    "contentType": [\n        "mcq",\n        "openEnded"\n    ]\n}', 'isBase64Encoded': False}
#     event = {
#     "version": "2.0",
#     "routeKey": "$default",
#     "rawPath": "/generateQuestion",
#     "rawQueryString": "",
#     "headers": {
#         "sec-fetch-mode": "cors",
#         "referer": "https://web.smartpaperapp.com/",
#         "content-length": "212",
#         "x-amzn-tls-version": "TLSv1.3",
#         "sec-fetch-site": "cross-site",
#         "x-forwarded-proto": "https",
#         "accept-language": "en-GB,en;q=0.9",
#         "origin": "https://web.smartpaperapp.com",
#         "x-forwarded-port": "443",
#         "x-forwarded-for": "43.241.194.168",
#         "accept": "application/json, text/plain, */*",
#         "x-amzn-tls-cipher-suite": "TLS_AES_128_GCM_SHA256",
#         "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
#         "x-amzn-trace-id": "Root=1-671d2347-311e66477e51d005528fdd92",
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": "\"Linux\"",
#         "host": "4bf5c7dxjn3e3e6wrgxbypjexu0acnjw.lambda-url.ap-south-1.on.aws",
#         "content-type": "application/json",
#         "accept-encoding": "gzip, deflate, br, zstd",
#         "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
#         "sec-fetch-dest": "empty"
#     },
#     "requestContext": {
#         "accountId": "anonymous",
#         "apiId": "4bf5c7dxjn3e3e6wrgxbypjexu0acnjw",
#         "domainName": "4bf5c7dxjn3e3e6wrgxbypjexu0acnjw.lambda-url.ap-south-1.on.aws",
#         "domainPrefix": "4bf5c7dxjn3e3e6wrgxbypjexu0acnjw",
#         "http": {
#             "method": "POST",
#             "path": "/generateQuestion",
#             "protocol": "HTTP/1.1",
#             "sourceIp": "43.241.194.168",
#             "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
#         },
#         "requestId": "bd3185df-19b5-405a-956d-c05be89e6084",
#         "routeKey": "$default",
#         "stage": "$default",
#         "time": "26/Oct/2024:17:13:43 +0000",
#         "timeEpoch": 1729962823787
#     },
#     "body": "{\"gradeLevel\":\"grade7\",\"subject\":\"Mathematics\",\"educationBoard\":\"CBSE\",\"topic\":\"Probabilty\",\"numberOfQuestions\":5,\"mcq\":true,\"openEnded\":true,\"userId\":\"66d176665d3a75527a7a161e\",\"contentType\":[\"mcq\",\"openEnded\"]}",
#     "isBase64Encoded": False
# }
#     event = {
#     "version": "2.0",
#     "routeKey": "$default",
#     "rawPath": "/latexToImage",
#     "rawQueryString": "",
#     "headers": {
#         "content-length": "263",
#         "x-amzn-tls-version": "TLSv1.3",
#         "x-forwarded-proto": "https",
#         "postman-token": "671e8da0-0a53-4124-afcd-e842a893d3fc",
#         "x-forwarded-port": "443",
#         "x-forwarded-for": "43.241.194.168",
#         "accept": "*/*",
#         "x-amzn-tls-cipher-suite": "TLS_AES_128_GCM_SHA256",
#         "x-amzn-trace-id": "Root=1-671fe1a6-1c356b76122244ed569fe31a",
#         "host": "4bf5c7dxjn3e3e6wrgxbypjexu0acnjw.lambda-url.ap-south-1.on.aws",
#         "content-type": "application/json",
#         "cache-control": "no-cache",
#         "accept-encoding": "gzip, deflate, br",
#         "user-agent": "PostmanRuntime/7.37.3"
#     },
#     "requestContext": {
#         "accountId": "anonymous",
#         "apiId": "4bf5c7dxjn3e3e6wrgxbypjexu0acnjw",
#         "domainName": "4bf5c7dxjn3e3e6wrgxbypjexu0acnjw.lambda-url.ap-south-1.on.aws",
#         "domainPrefix": "4bf5c7dxjn3e3e6wrgxbypjexu0acnjw",
#         "http": {
#             "method": "POST",
#             "path": "/latexToImage",
#             "protocol": "HTTP/1.1",
#             "sourceIp": "43.241.194.168",
#             "userAgent": "PostmanRuntime/7.37.3"
#         },
#         "requestId": "f243eb97-085d-4987-9f58-27e4249bd2f8",
#         "routeKey": "$default",
#         "stage": "$default",
#         "time": "28/Oct/2024:19:10:30 +0000",
#         "timeEpoch": 1730142630294
#     },
#     "body": "[{\n    \"queId\":\"demo-queId\",\n    \"questionText\":\"Simplifying numerator: $(3x+4)(2x-5)$    $= 6x^2 + 8x - 15x - 20$ (Applying distributive)    $= 6x^2 - 7x - 20$     $-1$ property)    Simplifying denominator: $(x^2-9)\",\n    \"markupFormat\":\"latex\",\n    \"width\":8\n}]",
#     "isBase64Encoded": False
# }


    event = {}
    context = {}
    result = message_handler(event=event, context=context)
    if (os.environ['cloudWatch'] == "True"):
        print(result)
    ## last deployment: 984498058219.dkr.ecr.ap-south-1.amazonaws.com/gen_ai_proxy_dev@sha256:d640348ca746b0a0372fd32a7037890a6bb913f83b3f6be6bd6e2ea67590463a