# from dotenv import load_dotenv
# load_dotenv(".env.dev")

from engine.core.llm_number_prediction import predict_llm_number
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
 
#     event = {
#     "Records": [
#         {
#             "messageId": "e0598b01-5a55-452e-a651-29a5e689942d",
#             "receiptHandle": "AQEBUSYQnljzswnOKQh/xwgzqiL0aworvCzshO/oJTFqpXkWZXTdNd6g39ZNsrdYgtEIOxRAOvWhhrSOkQKSyrQaHDBaPOrbzcEd31Hu6sN/vmA8JNTNBclm166xWCxiHmhD+9QIp6kVoGBughN0b/mHo3ncYvYGWgfey/uJXV0QUXIiN/cKveToilxMOyz+CeKlt+fhT5OIyFqenwVbJjmK+2urHDDnftPB3TIPxxBXZ5Z32vaz58cYTnpFB4EsNxrfdXpCTZ+RqvkBEKdp4JySXchJwDmvZHnyFYV53CnLHx4ERvIOAsUiBMlo3umFlnO2Pk+jN7/WKOxlrnzKBDj8f53CeL/RDR3l+Qx2ixyY4Eqtu2gsSCoY7o3uT66DWOBc96NToNQm5n5FiLl51flkG/5oi6Y1/jbaQ+pXupM38tI=",
#             "body": "[{\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"Measure the angles of a triangle that has sides of lengths 3 cm, 4 cm, and 5 cm.\", \"studentAnswer\": \"\\\"The triangles with lengths - 3cm, 4cm & 5cm\\n\\nThe triangle satisfies 3\\u00b2 + 4\\u00b2 = 25 = 5\\u00b2 \\u2192 Pythagorean theorem.\\n\\nThe first angle is will be 90\\u00b0 which is opposite to the length 5cm.\\n\\nAngle opp. to 3cm \\u21d2 sin\\u03b8 = opp. = 3 \\u2234 \\u03b8 = 36.87\\u00b0\\n                        hypo.   5\\n\\nNow as \\u03b8 = 36.87\\u00b0 & 90\\u00b0 \\u2234\\nlast angle = 180 - 36.87 - 90\\u00b0 = 53.13\\u00b0\\\"\", \"rubrics\": [{\"rubricId\": \"c960c744-c873-4e31-bbd5-e62fc272cb68\", \"score\": 1, \"criteria\": \"Correctly identifies that the triangle is a right-angled triangle (since 3\\u00b2 + 4\\u00b2 = 5\\u00b2, satisfying the Pythagorean theorem).\"}, {\"rubricId\": \"42ad5339-f7c2-4c84-80b3-1ae5c6ba3122\", \"score\": 1, \"criteria\": \"Correctly determines that the right angle is opposite the side of length 5 cm (i.e., 90\\u00b0).\"}, {\"rubricId\": \"baffa790-b9af-421c-bd04-4c5eda5fa111\", \"score\": 1, \"criteria\": \"Correctly calculates the angle opposite the side of length 3 cm as 36.87\\u00b0 using trigonometric functions (or sine/cosine rule).\"}, {\"rubricId\": \"a8ca8dcf-ad7e-404f-97e9-c22c032ad17c\", \"score\": 1, \"criteria\": \"Correctly calculates the angle opposite the side of length 4 cm as 53.13\\u00b0 (since the sum of angles in a triangle is 180\\u00b0).\"}], \"maxScore\": 4, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/master/67038612fe605db1a332ba7a/xOqh6vPeXLGF3qMQhWLTg/ans_crop/ec0dbff0-2f0e-45ea-8705-aed8b9330084.webp\"}, \"gradingPrompt\": \"gpt-ocr\", \"status\": \"processing\", \"student_id\": \"IfoHF2t1eZW4Z22UQD8eY\", \"scan_id\": \"xOqh6vPeXLGF3qMQhWLTg\", \"que_id\": \"5ca22a6c-dfe8-410c-b4eb-911393b73391\"}]",
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
#             "body": "[{\"modelName\": \"claude-vision-ocr\", \"subject\": \"Mathematics\", \"retryFlag\": \"both\", \"questionInfo\": {\"question\": \"Simplify the expression: (3x + 4)(2x - 5)/(x\\u00b2 - 9)\", \"studentAnswer\": \"{6x^2 - 7x - 20}\", \"rubrics\": [{\"rubricId\": \"L0Bkg3bdyucbZCmDspQyy\", \"score\": 1, \"criteria\": \"1 mark for correctly identifying or factoring x\\u00b2 - 9 as a difference of squares: x\\u00b2 - 9 = (x+3)(x-3)\"}, {\"rubricId\": \"73c3eaa8-6936-4f24-af60-b31559fa6cad\", \"score\": 1, \"criteria\": \"1 mark for correctly expanding the product of the two binomials (3\\ud835\\udc65+4)(2\\ud835\\udc65\\u22125) using the distributive property (FOIL): (3\\ud835\\udc65+4)(2\\ud835\\udc65\\u22125)  = 6x\\u00b2 -15\\ud835\\udc65 +8\\ud835\\udc65 -20 = 6x\\u00b2  - 7\\ud835\\udc65 -20\"}, {\"rubricId\": \"71dbc04d-2c40-409d-b51d-a7366e30ac35\", \"score\": 1, \"criteria\": \"1 mark for dividing the expanded expression (6x\\u00b2  - 7\\ud835\\udc65 -20) with the factored form (x+3)(x-3) and simplifying: (6x\\u00b2  - 7\\ud835\\udc65 -20)/((x+3)(x-3))\"}], \"maxScore\": 3, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/master/670ce597f675325652b1850f/KrMlyDSsgUZmL6dtO8ONX/ans_crop/6cdfaa4a-eb5a-40da-8380-b513615420bd.webp\"}, \"gradingPrompt\": \"claude-ocr\", \"status\": \"processing\", \"student_id\": \"WyYdZ1hcGf0moeMpA2Kqm\", \"scan_id\": \"N7rQKHDS8H3Hi8dcPyCNH\", \"que_id\": \"wapb-n7DgS_caZ2zv3lDK\"}]",
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


#     event = {
#     "version": "2.0",
#     "routeKey": "$default",
#     "rawPath": "/latexToImage",
#     "rawQueryString": "",
#     "headers": {
#         "sec-fetch-mode": "cors",
#         "referer": "http://localhost:3000/",
#         "content-length": "211",
#         "x-amzn-tls-version": "TLSv1.3",
#         "sec-fetch-site": "cross-site",
#         "x-forwarded-proto": "https",
#         "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
#         "origin": "http://localhost:3000",
#         "x-forwarded-port": "443",
#         "x-forwarded-for": "103.249.38.34",
#         "pragma": "no-cache",
#         "accept": "*/*",
#         "x-amzn-tls-cipher-suite": "TLS_AES_128_GCM_SHA256",
#         "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
#         "x-amzn-trace-id": "Root=1-6729a24e-54e3b65b016a9d043705e185",
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": "\"macOS\"",
#         "host": "4bf5c7dxjn3e3e6wrgxbypjexu0acnjw.lambda-url.ap-south-1.on.aws",
#         "content-type": "text/plain;charset=UTF-8",
#         "cache-control": "no-cache",
#         "accept-encoding": "gzip, deflate, br, zstd",
#         "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
#         "sec-fetch-dest": "empty"
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
#             "sourceIp": "103.249.38.34",
#             "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
#         },
#         "requestId": "835c92c4-40dc-4ad0-99de-9c1ea0488b9b",
#         "routeKey": "$default",
#         "stage": "$default",
#         "time": "05/Nov/2024:04:42:54 +0000",
#         "timeEpoch": 1730781774372
#     },
#     "body": "[{\"queId\":\"demo-queId\",\"questionText\":\"We give illustrations for the {1 + 2} processes $e^+e^-$, gluon-gluon and $\\\\gamma\\\\gamma \\\\to W t\\\\bar b \\\\\\\\ c=\\\\pm\\\\sqrt{a^2 + b^2}.$\",\"markupFormat\":\"latex\",\"width\":8}]",
#     "isBase64Encoded": False
# }

#     event = {
#     "Records": [
#         {
#             "messageId": "54f4d3d2-f58e-423f-bf10-fb188af84049",
#             "receiptHandle": "AQEBj77/J69BORcxoOIWfq2ppn81IrcBfqEqWbY/lJrmF1ijt0awcZwiJY2mYCmYQnp8VHii/7RD6wT1CdwasnAh+BOT9GEanC9CNP9q5z7Mn2K4liRGwTpFEVsVqDf0tKuWkM959M1gdc+197Q8A9eGFOmkKQDY6E/PD4jn9A/AqrmW9hmUTrpvu5zkj2XWPLke1YQDMyZad7ghJq61oiYSryrXg+JaNwLQKGM+BFb8grr4TdzX4HhgDA4XvOncNm3Si/CMAW+2iaHoFZ1NtLSbMtaK7sOIargj8yHNG4p+dsrg/Zw34NH4aCUIVszw+VpVJbtfbJtNbykg7nqKKYyk6AGYErnPLNuS3tebDGBtLAddCcj2CFoZF+9qsRtVi0UpuXMA6xOte+boGM8olkaDmTHwr45YdXY0DLVqw2Khl+I=",
#             "body": "[{\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"10 + 19 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"29\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/015480b0-72aa-4813-b404-61a6d1013cb2.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"8ZdpFGZ-vrNtIIR3fsSt_\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"19 + 1 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"20\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/0608d0f7-5531-436a-874d-dda345278bfd.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"Dw-yu-J0ddxPdyxALfprH\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"8 + 9 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"17\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/75c070b0-4c8c-4b7d-ba73-0c9be8096b44.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"MhU--ULjXxGdCHWgR41ax\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"11 + 3 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"14\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/ad12c74b-914b-4690-9335-b9c4d5f41ff0.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"kGiyMNyqvyhELG2WdD1N_\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"11 + 5 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"16\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/418837e9-3117-461c-8181-f71e2f625354.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"2UlNayqaf58HRSUmjwK9N\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"19 + 16 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"35\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/5f8431a1-5fa8-48d4-996c-2b2a1cda48aa.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"2q8GLAlRI7AUFRaWyEAdc\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"6 + 15 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"21\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/4bec5070-64eb-432b-b048-dc831b0047d9.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"ZM8GXlPeAMB1M-j1m2jxm\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"19 + 13 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"32\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/6c368308-5a6e-4b7d-81a1-e8c87f85acf5.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"8nfBLJlLpimn4bh8CotSD\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"4 + 13 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"17\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/c2829010-d61f-46f7-9807-3d588d1fbd8c.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"C9wHOJzOg4Wr9xi39kyEQ\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"7 + 5 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"12\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/4c554261-e052-4065-be2a-0276a1a7fb8b.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"WJjwDIHp_f_NnC8BvcI2U\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"13 + 8 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"21\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/9120a227-4241-40a5-9493-a4888d79791e.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"JuE1glMGyy1VqAP_0ycha\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"8 + 18 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"26\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/74f81e59-d441-43e8-9fc1-9ee7f4507659.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"N6qSoy633Di6-mP94-D_I\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"12 + 3 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"15\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/9b8c96fe-554d-4b62-be22-4170bd124ddc.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"5vXkMfe8E_0BdVEw8qVMj\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"11 + 16 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"27\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/1c0a9bf8-200f-4fed-aadf-44f40b407918.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"Wfk8DbEo3UVc58Zp-gG4k\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"9 + 19 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"28\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/698d26e2-55d2-445f-8849-4e1b05472135.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"mbmEq4h1MFR7BybpdUkjn\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"11 + 15 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"26\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/6fa11984-2905-4231-a9c4-7d8391143382.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"Xn9RRieErR2rAsvqLAABA\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"4 + 18 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"22\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/4ad5fe85-08c0-4b87-8fc2-6643e8e3e9be.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"BnFRk5_-m7ewexjV0Ck9h\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"11 + 19 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"30\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/279eafd5-dd60-4c44-ad94-f1630974754c.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"aCSBryE_iC0xZi5botWgy\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"7 + 9 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"16\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/6916fd7f-73f2-48bd-82f6-fb96fc65b3f5.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"qMsNYYNHvfgJps990328Q\"}, {\"modelName\": \"ensamble-vision\", \"questionInfo\": {\"question\": \"17 + 8 =\", \"studentAnswer\": \"\", \"correctAnswer\": \"25\", \"rubrics\": [], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6729eb6ae5f23fa22ffcc854/RCzNWa-uCgPLfv7-itY68/ans_crop/ce41d428-00c9-44f3-8a97-3298af1adf3b.webp\"}, \"gradingPrompt\": \"default\", \"status\": \"processing\", \"subject\": \"maths\", \"scanId\": \"RCzNWa-uCgPLfv7-itY68\", \"studentId\": \"ZDPOgf3miKCETMdMUqBka\", \"queId\": \"-_vpTKc_J0nni5Qlh2AG_\"}]",
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "SentTimestamp": "1730808477044",
#                 "SenderId": "AIDA6KOFIGPVZCQQML6H3",
#                 "ApproximateFirstReceiveTimestamp": "1730808477050"
#             },
#             "messageAttributes": {},
#             "md5OfBody": "5e48ee1448647bc429b6775bbd9edf53",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:ap-south-1:984498058219:ai-serivce-llm-calling-queue-prod-new",
#             "awsRegion": "ap-south-1"
#         }
#     ]
# }

#     event = {
#     "version": "2.0",
#     "routeKey": "$default",
#     "rawPath": "/generateQuestion",
#     "rawQueryString": "",
#     "headers": {
#         "sec-fetch-mode": "cors",
#         "referer": "https://web.smartpaperapp.com/",
#         "content-length": "190",
#         "x-amzn-tls-version": "TLSv1.3",
#         "sec-fetch-site": "cross-site",
#         "x-forwarded-proto": "https",
#         "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
#         "origin": "https://web.smartpaperapp.com",
#         "x-forwarded-port": "443",
#         "x-forwarded-for": "103.39.129.202",
#         "pragma": "no-cache",
#         "accept": "application/json, text/plain, */*",
#         "x-amzn-tls-cipher-suite": "TLS_AES_128_GCM_SHA256",
#         "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
#         "x-amzn-trace-id": "Root=1-674fedfb-275d05f71b996b964d79c3d3",
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": "\"Linux\"",
#         "host": "4bf5c7dxjn3e3e6wrgxbypjexu0acnjw.lambda-url.ap-south-1.on.aws",
#         "content-type": "application/json",
#         "cache-control": "no-cache",
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
#             "sourceIp": "103.39.129.202",
#             "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
#         },
#         "requestId": "4a709753-4cd4-4e8d-b540-431270a4d76d",
#         "routeKey": "$default",
#         "stage": "$default",
#         "time": "04/Dec/2024:05:51:55 +0000",
#         "timeEpoch": 1733291515902
#     },
#     "body": "{\"gradeLevel\":\"grade11\",\"subject\":\"Mathematics\",\"educationBoard\":\"CBSE\",\"topic\":\"vector geometry\",\"numberOfQuestions\":5,\"userId\":\"66d176665d3a75527a7a161e\",\"contentType\":[\"mcq\",\"openEnded\"]}",
#     "isBase64Encoded": False
# }


#     event = {
#     "Records": [
#         {
#             "messageId": "3853ad41-432a-4610-9a02-951f1eac003b",
#             "receiptHandle": "AQEBOB4jSTjMJqAodnIjIfrps95PNzaudy3OTGG84jYToN3x6498dm5I6WWARcDe7hGtfJ6Qaov9347bGAlEokJ8iXm5GeaGYbZoECvl7zINHgAtQih+XaUcLfdiYdfOncAmSMrhUDhajlxFpKNdiz1rgFv/81CsZTTvSUU53m85uhEumQJPooAjLbP3wbyrxkdiS22KXeFTizXC1koSvdK2auGNsax2OjvAgPS0Hw/6cAgAO7Kb4F8c/3ASjeKZPNvCN8xv/cLyd+FQqRGa24NFQmikFCniV/EDFzfR6UvTDV45INydoXlkoS7ODqR2vjY9KSkTmEXlQIZZ0HjYrz3hhzoQS75wyp+B74dVepDlsFiAu68shKIcPgfckcd04I+y06nvGwOjenuSeJ997b1VqThVjdNwfZ8cVwv4WikMYEc=",
#             "body": "[{\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"Draw and label a simple diagram of a plant cell, indicating at least five main parts.\", \"studentAnswer\": \"\", \"rubrics\": [{\"score\": 1, \"criteria\": \"Draw the overall rectangular or angular shape to represent the plant cell structure.\", \"rubricId\": \"S65LzCf8mHFHJY58kntqp\"}, {\"score\": 1, \"criteria\": \"Label 'Cell Wall' and 'Cell Membrane' accurately on the diagram.\", \"rubricId\": \"HuYp9gsuBnJX3V-thQksH\"}, {\"score\": 1, \"criteria\": \"Label the 'Nucleus' within the cell.\", \"rubricId\": \"O4Dp30gg6lj3jeJQVMH7T\"}, {\"score\": 1, \"criteria\": \"Label at least one 'Chloroplast' correctly.\", \"rubricId\": \"yCMyBbh7ERkNTgM6jlTb3\"}, {\"score\": 1, \"criteria\": \"Include and label a 'Vacuole' within the cell.\", \"rubricId\": \"LAKiOpQFYSjOslk7iczlD\"}], \"maxScore\": 5, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/67723b4e6743128c5238b6fd/NzXaXEE9KqqUwDx0Vm9g4/ans_crop/9be0b200-e480-441f-a66b-f5dc8b2fb439.webp\"}, \"gradingPrompt\": \"gpt-ocr\", \"status\": \"processing\", \"subject\": \"biology\", \"scanId\": \"NzXaXEE9KqqUwDx0Vm9g4\", \"studentId\": \"8YeSUWX0E2x1AIXUcGt-O\", \"queId\": \"yL5pu_xM08rdQcgxEMdCs\"}, {\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"Illustrate a simple diagram of the human heart and label the four chambers.\", \"studentAnswer\": \"\", \"rubrics\": [{\"score\": 1, \"criteria\": \"Draw a simplified shape representing the human heart.\", \"rubricId\": \"uRG1s1IWfY6NOsc7q_LAH\"}, {\"score\": 1, \"criteria\": \"Label the 'Left Atrium' and 'Right Atrium' correctly on the top part of the heart.\", \"rubricId\": \"q0cFuOFmJFZKify6X8ZaL\"}, {\"score\": 1, \"criteria\": \"Label the 'Left Ventricle' on the bottom part of the heart.\", \"rubricId\": \"VN0yTFiZzsvfp0v3RhPyd\"}, {\"score\": 1, \"criteria\": \"Label the 'Right Ventricle' on the bottom part of the heart.\", \"rubricId\": \"yazdHyRW3j86edNS6sazY\"}], \"maxScore\": 4, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/67723b4e6743128c5238b6fd/NzXaXEE9KqqUwDx0Vm9g4/ans_crop/c0e6b38c-e412-4692-8379-aa4f98548c62.webp\"}, \"gradingPrompt\": \"gpt-ocr\", \"status\": \"processing\", \"subject\": \"biology\", \"scanId\": \"NzXaXEE9KqqUwDx0Vm9g4\", \"studentId\": \"8YeSUWX0E2x1AIXUcGt-O\", \"queId\": \"v3QGHK5Arv4jc_54io4vy\"}]",
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "AWSTraceHeader": "Root=1-67736fff-4efef9a5179d93ad3883767f;Parent=553750f7e8d7e508;Sampled=0;Lineage=1:e9c0ad2b:0",
#                 "SentTimestamp": "1735618568222",
#                 "SenderId": "AIDA6KOFIGPVZCQQML6H3",
#                 "ApproximateFirstReceiveTimestamp": "1735618568223"
#             },
#             "messageAttributes": {},
#             "md5OfBody": "f289000c7d6ff45c423323d844d62e47",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:ap-south-1:984498058219:ai-serivce-llm-calling-queue-staging",
#             "awsRegion": "ap-south-1"
#         }
#     ]
# }
#     event = {
#     "Records": [
#         {
#             "messageId": "eeef11e1-54b4-48bd-88c5-59e21d7e9a03",
#             "receiptHandle": "AQEB3UxuQh8S7kMDFZEYkHndB5mQILSi5Q91IpeiKtBr+T5TwT/uw25TdPnDo0PHqfio4Xl4RSORS2nOU6rfq2GKH0LgEQUrGGaAlwm3zIfn6OrVop2Bd4RGTkmvB+OWETm/yPLLaQq3rfCgG3VdXlsksZcmjujnOh+qd+v8afUGVD4ixvct6/jNCn+qx9nxOwpseXr5pqjVWhca0am/Bv00oMbP7u9xIfIOlOqfLlvQLxkd47rM9wLtKi8QHN2ifLWl1Jx48nV0qZqU4Q4oSBQG1U6ZOJ7neQx6vgAIHhdhG++bd+eMB2v/V8MfCRiHWql+TBEqsWJAkA8ujnRlcSsj7aaNM24vpYqlePfqrHJ2tt8BdS8k1eUnTtO7zpNwxvlm7X7spBnYpAGJC3M4vgsymaXEA+IqsPwTgGw+WC2kh4s=",
#             "body": "[{\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"Write the following using numbers, literals and signs of basic operations:\\n(i) The sum of 6 and x.\\n(ii) 3 more than a number y.\\n(iii) One-third of a number x.\\n(iv) One-half of the sum of number x and y.\\n(v) Number y less than a number 7.\\n(vi) 7 taken away from x\\n(vii) 2 less than the quotient of x and y\\n(viii)4 times x taken away from one-third of y \\n(ix) Quotient of x  by 3 is multiplied by y\", \"studentAnswer\": \"\", \"rubrics\": [{\"rubricId\": \"8JYmHd1qJD9SXhm5ri4v_\", \"score\": 1, \"criteria\": \"(i) The sum of 6 and x can be written as 6 + x\"}, {\"rubricId\": \"4ca798df-a174-4357-9b58-67d1755c4f96\", \"score\": 1, \"criteria\": \"(ii) 3 more than a number y can be written as y + 3\"}, {\"rubricId\": \"9885fa06-0cff-438c-a9b1-107b5cf18de3\", \"score\": 1, \"criteria\": \"(iii) One-third of a number x can be written as x/3\"}, {\"rubricId\": \"a26a1c10-1379-4ea7-b67d-effd75325e2c\", \"score\": 1, \"criteria\": \"(iv) One-half of the sum of number x and y can be written as (x + y)/ 2\"}, {\"rubricId\": \"ec18b93b-c804-408a-b868-c5a49feeddf5\", \"score\": 1, \"criteria\": \"(v) Number y less than a number 7 can be written as 7 \\u2013 y\"}, {\"rubricId\": \"79d0f99f-9783-49d4-a00f-388c61e18df1\", \"score\": 1, \"criteria\": \"(vi) 7 taken away from x can be written as x \\u2013 7\"}, {\"rubricId\": \"de7355d1-8715-4df6-94f7-8caff6649210\", \"score\": 1, \"criteria\": \"(vii) 2 less than the quotient of x and y can be written as x/y \\u2013 2\"}, {\"rubricId\": \"46324878-718c-495e-b6f5-f2518049443b\", \"score\": 1, \"criteria\": \"(viii) 4 times x taken away from one-third of y can be written as y/3 \\u2013 4x\"}, {\"rubricId\": \"ad7d4c4f-1035-42fd-9e48-c8cc0f8271d7\", \"score\": 1, \"criteria\": \"(ix) Quotient of x by 3 is multiplied by y can be written as xy/3\"}], \"maxScore\": 9, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6769554bb092531205d8c0b7/iAiqUPVgLK-ce1LDMBp3L/ans_crop/247f322a-0033-4326-876d-1fe2c436bae0.webp\"}, \"gradingPrompt\": \"gpt-ocr\", \"status\": \"processing\", \"subject\": \"mathematics\", \"scanId\": \"iAiqUPVgLK-ce1LDMBp3L\", \"studentId\": \"hGncUeqVbUkjTWfBbgNbE\", \"queId\": \"lmDAi9xiVMxm2INrzcTHA\"}, {\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"Think of a number. Multiply by 5. Add 6 to the result. Subtract y from this result. What is the result?\", \"studentAnswer\": \"\", \"rubrics\": [{\"rubricId\": \"VxPSBwXPtHw4xz77H4uAZ\", \"score\": 1, \"criteria\": \"Firstly assume a number and then operate give task in given order in question. Finally the expression should be like: 5x + 6 \\u2013 y\"}], \"maxScore\": 1, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6769554bb092531205d8c0b7/iAiqUPVgLK-ce1LDMBp3L/ans_crop/418cc8c5-8f82-4019-bc65-48d885290ac6.webp\"}, \"gradingPrompt\": \"gpt-ocr\", \"status\": \"processing\", \"subject\": \"mathematics\", \"scanId\": \"iAiqUPVgLK-ce1LDMBp3L\", \"studentId\": \"hGncUeqVbUkjTWfBbgNbE\", \"queId\": \"eXezjUFaDJnbE4dVtCLzi\"}]",
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "AWSTraceHeader": "Root=1-67737874-420342481a14da1a6009a4f5;Parent=7481d5209b99bb7d;Sampled=0;Lineage=1:e9c0ad2b:0",
#                 "SentTimestamp": "1735620732600",
#                 "SenderId": "AIDA6KOFIGPVZCQQML6H3",
#                 "ApproximateFirstReceiveTimestamp": "1735620732605"
#             },
#             "messageAttributes": {},
#             "md5OfBody": "7dd0469115d4470ab684da50f8d2e832",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:ap-south-1:984498058219:ai-serivce-llm-calling-queue-staging",
#             "awsRegion": "ap-south-1"
#         }
#     ]
# }

#     event = {
#     "Records": [
#         {
#             "messageId": "6b5574d5-f2d1-4a0c-a663-682e2557369f",
#             "receiptHandle": "AQEBPZ/ti3ELmm/gtk/KTIMHQ3U7iEpDl8FCI/9MwqfhAQd2vJWdWI0eicEVAJKclWPHhHKoKPL3wsxFAFXXD9wbIH8gX9miymVkDk8C4Xg/7Qd9mdyvgJIqhbMZGJyO5Lc8zxNb8Kao4GGfLikrYX6eLyoBBkntusT/6cwOypk5WFJc3+2Swj57I3DKyMMffaXfo1eStARmS4yKloY9psqPOKUy0hOtUnhcP+d/bMMTpkB1nYdZ0H6XGavqI1WPT+fK7nKB7rD1EpLHO+//QtYRpS3pMIRz98Rf3RJw6k2Ue4JElJ+7Vbj3OB2ytIfQpUPDqPRmvUlJtO6hSoaWmeRFCzuawaaam4iCfj+nlkcRDPFdxeG0UCQiiw9kWrXdC8pqW6V90fQ88Gl9BCyeXPJ/HUdC7ccbYNqoXcd7dTwvQFY=",
#             "body": "[{\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"Calculate the integral of the function `f(x) = 3x^2 + 2x + 1` with respect to `x`.\", \"studentAnswer\": \"\", \"rubrics\": [{\"score\": 1, \"criteria\": \"Correct integration of `3x^2` resulting in `x^3`.\", \"rubricId\": \"UkfBFgSiYnHedL7FS9Gg1\"}, {\"score\": 1, \"criteria\": \"Correct integration of `2x` resulting in `x^2`.\", \"rubricId\": \"pEhxdXOK7a-soYpUOJebW\"}, {\"score\": 1, \"criteria\": \"Correct integration of `1` resulting in `x`. Including constant of integration `C`.\", \"rubricId\": \"bzxC3d4nyhCxwFD5-W89p\"}], \"maxScore\": 3, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/676e3a071ef13ed9f02496cb/IRV6ovpsw5qjijUnuIFKd/ans_crop/8c7aceb6-ecfc-4aa0-8e55-e445f260aa0c.webp\"}, \"gradingPrompt\": \"gpt-ocr\", \"status\": \"processing\", \"subject\": \"mathematics\", \"scanId\": \"IRV6ovpsw5qjijUnuIFKd\", \"studentId\": \"8YeSUWX0E2x1AIXUcGt-O\", \"queId\": \"HXE_Z6-9PzJtCvGrjiVSL\"}, {\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"What is the value of `int 2x dx` from `0` to `3`?\", \"studentAnswer\": \"\", \"rubrics\": [{\"score\": 1, \"criteria\": \"Correct indefinite integration of `2x` to obtain `x^2`.\", \"rubricId\": \"sj8lKBY4sxxOsWA3TEFHq\"}, {\"score\": 1, \"criteria\": \"Correct evaluation of the definite integral from `0` to `3`.\", \"rubricId\": \"g8BIoUmlBYQ24l3LPdLew\"}], \"maxScore\": 2, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/676e3a071ef13ed9f02496cb/IRV6ovpsw5qjijUnuIFKd/ans_crop/0137112a-38d8-42a8-afaa-0bf3c48c93dc.webp\"}, \"gradingPrompt\": \"gpt-ocr\", \"status\": \"processing\", \"subject\": \"mathematics\", \"scanId\": \"IRV6ovpsw5qjijUnuIFKd\", \"studentId\": \"8YeSUWX0E2x1AIXUcGt-O\", \"queId\": \"ibHCtx56cdZSB7yVAWwlT\"}]",
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "AWSTraceHeader": "Root=1-67767fe0-5e2a87e26cdb5a2b72203f59;Parent=1a44e18ee6c2f680;Sampled=0;Lineage=1:e9c0ad2b:0",
#                 "SentTimestamp": "1735819239352",
#                 "SenderId": "AIDA6KOFIGPVZCQQML6H3",
#                 "ApproximateFirstReceiveTimestamp": "1735819239357"
#             },
#             "messageAttributes": {},
#             "md5OfBody": "35c3446d826ba2d6f9679708cadb4b40",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:ap-south-1:984498058219:ai-serivce-llm-calling-queue-staging",
#             "awsRegion": "ap-south-1"
#         }
#     ]
# }
#     event = {
#     "Records": [
#         {
#             "messageId": "e5a8b74c-f43e-46c1-ba32-3f3dd6a27bcb",
#             "receiptHandle": "AQEBgzder8JwZWfV/xjqFyJI1fg7tePhSFWNBmTe5dqx46wzJ+YjjqJbG8XWt7IFmC+k2BrByKhUsotdILco1OaiE03TG7IJpTapfFmVY40OFNKXY/RsBaXiaHGEdvHeV932H3N5jy/e1Qlkjv7vc7/Rs3/rQoSfRbdX2SFHN1ojVZOcRNtXNVO58p0nftpC1Ei9lZZq4Y8jiGm44fXFCOfgPt/V3xlN2F89TutoA1IpAGoyifdcpgEgTZZVxVSBCTRxFbUZsLdaL+G1xjHs9zoOurBbsoQ6UdYSHrkg7kwPwCA2ZNRnkU/lUz7jhLldLN/8Ni6GBXt3kJR118cAGWVPRoJb49tcttAja4ueGHM/2AeHsIV7QMvydXNCktY1qaVh/WkIjIFHV9xycFhjRjmcDCLjizGIwaRyCWLVfCgtoGo=",
#             "body": "[{\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"A rectangle has a perimeter of `66` meters. If the length of the rectangle is `3` meters more than twice the width, find the dimensions of the rectangle.\", \"studentAnswer\": \"\", \"rubrics\": [{\"score\": 1, \"criteria\": \"Correctly set up the equation for perimeter using given relationship: `2(l + w) = 66` and `l = 2w + 3`.\", \"rubricId\": \"7fDix0aGaYUAL0waaibLi\"}, {\"score\": 1, \"criteria\": \"Solve for one variable in terms of the other correctly and substitute back.\", \"rubricId\": \"ccEfrh8s8GCU-NPalpkQN\"}, {\"score\": 1, \"criteria\": \"Calculate correct dimensions of the rectangle: length = `23` meters, width = `10` meters.\", \"rubricId\": \"5bLfCJ-vlk6fDzcobyr_s\"}], \"maxScore\": 3, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/master/675185e99717e314b906e9bf/flt4neVScWnbN9hqqUKgQ/ans_crop/14f2d30f-2ce0-4aea-a659-088c992cb245.webp\"}, \"gradingPrompt\": \"gpt-ocr\", \"status\": \"processing\", \"subject\": \"mathematics\", \"scanId\": \"flt4neVScWnbN9hqqUKgQ\", \"studentId\": \"NmIZca-Ft1MXU1fNnvAhk\", \"queId\": \"us_uH89TkF-SlmMZxrT5Y\"}, {\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"The area of a trapezium is `144` square cm. If the two parallel sides are `12` cm and `20` cm, find the height of the trapezium.\", \"studentAnswer\": \"\", \"rubrics\": [{\"score\": 1, \"criteria\": \"Correctly set up the area formula for a trapezium: `(1/2) * (a + b) * h = 144`.\", \"rubricId\": \"HMH-HxsWWFbvS54Q9p2hr\"}, {\"score\": 1, \"criteria\": \"Solve for the height correctly using given area and side lengths.\", \"rubricId\": \"bWxCQUINSG71cTzbWWK3L\"}], \"maxScore\": 2, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/master/675185e99717e314b906e9bf/flt4neVScWnbN9hqqUKgQ/ans_crop/374c7031-7033-40fe-bf4b-35e4d80c7739.webp\"}, \"gradingPrompt\": \"gpt-ocr\", \"status\": \"processing\", \"subject\": \"mathematics\", \"scanId\": \"flt4neVScWnbN9hqqUKgQ\", \"studentId\": \"NmIZca-Ft1MXU1fNnvAhk\", \"queId\": \"Rf924iEosCR93MP6Shqw0\"}, {\"modelName\": \"gpt-ocr-vision\", \"questionInfo\": {\"question\": \"Find the angle `x` if `sin(x)` = `0.5`. Assume `x` is between `0` and `360` degrees.\", \"studentAnswer\": \"\", \"rubrics\": [{\"score\": 1, \"criteria\": \"Identify the reference angle correctly using the value of `sin(x) = 0.5`.\", \"rubricId\": \"k2MDBYI0PeGCde_uefQlR\"}, {\"score\": 1, \"criteria\": \"Calculate the correct angles `x = 30 degrees` and `x = 150 degrees`.\", \"rubricId\": \"SYTaeH3fRdd43E1ehNfp1\"}], \"maxScore\": 2, \"studentAnswerUrl\": \"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/master/675185e99717e314b906e9bf/flt4neVScWnbN9hqqUKgQ/ans_crop/f994d81c-25e1-4e20-9f2e-0a2249a90a7e.webp\"}, \"gradingPrompt\": \"gpt-ocr\", \"status\": \"processing\", \"subject\": \"mathematics\", \"scanId\": \"flt4neVScWnbN9hqqUKgQ\", \"studentId\": \"NmIZca-Ft1MXU1fNnvAhk\", \"queId\": \"JHrS3N-2guiYbPRPZ72dE\"}]",
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "AWSTraceHeader": "Root=1-677d79cd-255afc964a36656421d3f599;Parent=6ad664af82b9e2d5;Sampled=0;Lineage=1:5625e7f4:0",
#                 "SentTimestamp": "1736276433637",
#                 "SenderId": "AIDA6KOFIGPVZCQQML6H3",
#                 "ApproximateFirstReceiveTimestamp": "1736276433638"
#             },
#             "messageAttributes": {},
#             "md5OfBody": "170fd63e80cf71befbd6adfa7195b339",
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
    ## last deployment: 984498058219.dkr.ecr.ap-south-1.amazonaws.com/gen_ai_proxy_dev@sha256:d640348ca746b0a0372fd32a7037890a6bb913f83b3f6be6bd6e2ea67590463a