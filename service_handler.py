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

    # if ('receivedAt' not in reqobj or reqobj['receivedAt'] == ''):
     # reqobj['receivedAt'] = datetime.now().isoformat()
    reqobj['receivedAt'] = datetime.utcnow().isoformat()

    return reqobj

if __name__ == "__main__":

#     event ={
#     "version": "2.0",
#     "routeKey": "$default",
#     "rawPath": "/generate",
#     "rawQueryString": "",
#     "headers": {
#         "sec-fetch-mode": "cors",
#         "referer": "https://dev.smartpaperapp.com/",
#         "content-length": "617",
#         "x-amzn-tls-version": "TLSv1.3",
#         "sec-fetch-site": "cross-site",
#         "x-forwarded-proto": "https",
#         "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
#         "origin": "https://dev.smartpaperapp.com",
#         "x-forwarded-port": "443",
#         "x-forwarded-for": "103.39.129.223",
#         "accept": "application/json, text/plain, */*",
#         "x-amzn-tls-cipher-suite": "TLS_AES_128_GCM_SHA256",
#         "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
#         "x-amzn-trace-id": "Root=1-66756050-1094984403e50b2e2f02212c",
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": "\"Linux\"",
#         "host": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "content-type": "application/json",
#         "accept-encoding": "gzip, deflate, br, zstd",
#         "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
#         "sec-fetch-dest": "empty"
#     },
#     "requestContext": {
#         "accountId": "anonymous",
#         "apiId": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "domainName": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "domainPrefix": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "http": {
#             "method": "POST",
#             "path": "/generate",
#             "protocol": "HTTP/1.1",
#             "sourceIp": "103.39.129.223",
#             "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
#         },
#         "requestId": "08b190ea-fdc4-4aa6-968e-458bd9d75b35",
#         "routeKey": "$default",
#         "stage": "$default",
#         "time": "21/Jun/2024:11:13:20 +0000",
#         "timeEpoch": 1718968400191
#     },
#     "body": "{\"modelName\":\"gpt-vision\",\"questionInfo\":{\"question\":\"Paula weeded 40% of her garden in\\n8 minutes. How many minutes will it\\ntake her to weed all of her garden at\\nthis rate? Explain.\",\"rubrics\":[{\"rubricId\":\"0cb2ebf7-21ff-4d7b-973f-bf510d9a77aa\",\"score\":1,\"criteria\":\"finding per minute rate at which Paula weeded the garden \"},{\"rubricId\":\"dfbe5678-0cab-46ee-ac58-770d40677bbe\",\"score\":1,\"criteria\":\"calaculate the time required to weed complete garden\"}],\"maxScore\":\"2\",\"studentAnswer\":\"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6675335e5f2d3bb3fe0f650b/4d938c9d-f37f-439d-959c-f652ca7eab3f/ans_crop/350da453-edf7-4572-8cba-268c62137445.webp\"},\"gradingPrompt\":\"ocr\"}",
#     "isBase64Encoded": False
# }
#     event = {
#     "version": "2.0",
#     "routeKey": "$default",
#     "rawPath": "/generate",
#     "rawQueryString": "",
#     "headers": {
#         "sec-fetch-mode": "cors",
#         "referer": "https://dev.smartpaperapp.com/",
#         "content-length": "464",
#         "x-amzn-tls-version": "TLSv1.3",
#         "sec-fetch-site": "cross-site",
#         "x-forwarded-proto": "https",
#         "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
#         "origin": "https://dev.smartpaperapp.com",
#         "x-forwarded-port": "443",
#         "x-forwarded-for": "103.39.129.223",
#         "accept": "application/json, text/plain, */*",
#         "x-amzn-tls-cipher-suite": "TLS_AES_128_GCM_SHA256",
#         "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
#         "x-amzn-trace-id": "Root=1-6679497b-7fb9ae4b736c3e606a793a62",
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": "\"Linux\"",
#         "host": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "content-type": "application/json",
#         "accept-encoding": "gzip, deflate, br, zstd",
#         "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
#         "sec-fetch-dest": "empty"
#     },
#     "requestContext": {
#         "accountId": "anonymous",
#         "apiId": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "domainName": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "domainPrefix": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "http": {
#             "method": "POST",
#             "path": "/generate",
#             "protocol": "HTTP/1.1",
#             "sourceIp": "103.39.129.223",
#             "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
#         },
#         "requestId": "584988d3-cbc4-4d81-b620-3f91dc00c297",
#         "routeKey": "$default",
#         "stage": "$default",
#         "time": "24/Jun/2024:10:24:59 +0000",
#         "timeEpoch": 1719224699616
#     },
#     "body": "{\"modelName\":\"gpt-vision\",\"gradingPrompt\":\"essay\",\"questionInfo\":{\"question\":\"\",\"rubrics\":[{\"rubricId\":\"5c95a384-c3e3-4083-8b7d-41ce55036418\",\"score\":1,\"criteria\":\"Correct Answer is option C 0.04, if it is marked give full point otherwise 0 points\"}],\"maxScore\":1,\"studentAnswer\":\"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/66792b68130c79540e3ef939/7c939fe3-ad51-40f4-9039-68749ca58212/ans_crop/95d70a9e-b7da-49bc-b079-74d4bef23501.webp\"}}",
#     "isBase64Encoded": False
# }


#     event = {
#     "version": "2.0",
#     "routeKey": "$default",
#     "rawPath": "/generate",
#     "rawQueryString": "",
#     "headers": {
#         "sec-fetch-mode": "cors",
#         "referer": "https://dev.smartpaperapp.com/",
#         "content-length": "595",
#         "x-amzn-tls-version": "TLSv1.3",
#         "sec-fetch-site": "cross-site",
#         "x-forwarded-proto": "https",
#         "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
#         "origin": "https://dev.smartpaperapp.com",
#         "x-forwarded-port": "443",
#         "x-forwarded-for": "103.39.129.223",
#         "accept": "application/json, text/plain, */*",
#         "x-amzn-tls-cipher-suite": "TLS_AES_128_GCM_SHA256",
#         "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
#         "x-amzn-trace-id": "Root=1-66792b92-62fdf0b15e015677656d60d7",
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": "\"Linux\"",
#         "host": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "content-type": "application/json",
#         "accept-encoding": "gzip, deflate, br, zstd",
#         "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
#         "sec-fetch-dest": "empty"
#     },
#     "requestContext": {
#         "accountId": "anonymous",
#         "apiId": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "domainName": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "domainPrefix": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "http": {
#             "method": "POST",
#             "path": "/generate",
#             "protocol": "HTTP/1.1",
#             "sourceIp": "103.39.129.223",
#             "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
#         },
#         "requestId": "37c00bd6-9fe0-4035-9fc8-9a8194f478fb",
#         "routeKey": "$default",
#         "stage": "$default",
#         "time": "24/Jun/2024:08:17:22 +0000",
#         "timeEpoch": 1719217042727
#     },
#     "body": "{\"modelName\":\"gpt-vision\",\"gradingPrompt\":\"default\",\"questionInfo\":{\"question\":\"A fruit salad contains 40% grapes. show 40% on the grid.\",\"rubrics\":[{\"rubricId\":\"6b9dc0d5-ed08-414f-95bc-f864b9797361\",\"score\":1,\"criteria\":\"40 % area of the grid is marked, so ideally 4 rows or 4 columns are marked\"}],\"maxScore\":1,\"studentAnswerUrl\":\"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/667a33b57100b0bbf8b52ff7/5e642c31-4f86-4e05-915f-c8cbf69e8623/ans_crop/6c7d3d88-5ba7-4330-8703-0b9e07422de8.webp\",\"studentAnswer\":\"\"}}",
#     "isBase64Encoded": False
# }
#     event = {
#     "version": "2.0",
#     "routeKey": "$default",
#     "rawPath": "/generate",
#     "rawQueryString": "",
#     "headers": {
#         "sec-fetch-mode": "cors",
#         "referer": "https://dev.smartpaperapp.com/",
#         "content-length": "595",
#         "x-amzn-tls-version": "TLSv1.3",
#         "sec-fetch-site": "cross-site",
#         "x-forwarded-proto": "https",
#         "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
#         "origin": "https://dev.smartpaperapp.com",
#         "x-forwarded-port": "443",
#         "x-forwarded-for": "103.39.129.223",
#         "accept": "application/json, text/plain, */*",
#         "x-amzn-tls-cipher-suite": "TLS_AES_128_GCM_SHA256",
#         "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
#         "x-amzn-trace-id": "Root=1-66792b92-62fdf0b15e015677656d60d7",
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": "\"Linux\"",
#         "host": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "content-type": "application/json",
#         "accept-encoding": "gzip, deflate, br, zstd",
#         "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
#         "sec-fetch-dest": "empty"
#     },
#     "requestContext": {
#         "accountId": "anonymous",
#         "apiId": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "domainName": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "domainPrefix": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "http": {
#             "method": "POST",
#             "path": "/generate",
#             "protocol": "HTTP/1.1",
#             "sourceIp": "103.39.129.223",
#             "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
#         },
#         "requestId": "37c00bd6-9fe0-4035-9fc8-9a8194f478fb",
#         "routeKey": "$default",
#         "stage": "$default",
#         "time": "24/Jun/2024:08:17:22 +0000",
#         "timeEpoch": 1719217042727
#     },
#     "body": "{\"modelName\":\"gpt-4-latest\",\"gradingPrompt\":\"default\",\"questionInfo\":{\"question\":\"After a brief medical examination a healthy couple came to know that the wife is unable to produce a functional gametes and therefore should look for an  Assisted Reproductive Technique. Name the 'ART' and the procedure involved that you can suggest to them to help the couple bear a child.\",\"rubrics\":[{\"rubricId\":\"6b9dc0d5-ed08-414f-95bc-f864b9797361\",\"score\":1,\"criteria\":\"The ART that would help the couple to bear a child is IVF (In Vitro Fertilisation) or Test tube baby programme. In this process, ova from donor female and sperms from the husband is collected and fused to form zygote in the laboratory under simulated conditions as in the body.  (OR) The ART that would help the couple to bear a child is Gamete intra fallopian transfer (GIFT), which is an In Vivo Fertilisation method.\"},{\"rubricId\":\"6fc76dd7-2a07-4deb-b060-90dc9e762c1a\",\"score\":0.5,\"criteria\":\"Zygote or early embryo (up to 8 blastomeres) is transferred into Fallopian tube  ZIFT. (OR) Ovum from a doner is taken and transferred into the fallopian tube of the wife.\"},{\"rubricId\":\"d67944f9-83a0-4a78-a44a-fe709500344f\",\"score\":0.5,\"criteria\":\"If embryo more than 8 blastomeres is transferred into the uterus IUT. (OR) Fertilisation will occur naturally inside the fallopian tube.\"}],\"maxScore\":2,\"studentAnswerUrl\":\"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/666959a6fad2af990c715996/a5d774e3-01e6-4c86-b6c6-6b0767151f40/ans_crop/bb86f4b4-87bf-46b5-a4f2-37e0227d48b7.webp\",\"studentAnswer\":\"\"}}",
#     "isBase64Encoded": False
# }
#     event = {
#     "version": "2.0",
#     "routeKey": "$default",
#     "rawPath": "/generate",
#     "rawQueryString": "",
#     "headers": {
#         "sec-fetch-mode": "cors",
#         "referer": "https://dev.smartpaperapp.com/",
#         "content-length": "2213",
#         "x-amzn-tls-version": "TLSv1.3",
#         "sec-fetch-site": "cross-site",
#         "x-forwarded-proto": "https",
#         "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
#         "origin": "https://dev.smartpaperapp.com",
#         "x-forwarded-port": "443",
#         "x-forwarded-for": "103.39.129.223",
#         "pragma": "no-cache",
#         "accept": "application/json, text/plain, */*",
#         "x-amzn-tls-cipher-suite": "TLS_AES_128_GCM_SHA256",
#         "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
#         "x-amzn-trace-id": "Root=1-667bf82f-67db39896830d6ee4dec5aed",
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": "\"Linux\"",
#         "host": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "content-type": "application/json",
#         "cache-control": "no-cache",
#         "accept-encoding": "gzip, deflate, br, zstd",
#         "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
#         "sec-fetch-dest": "empty"
#     },
#     "requestContext": {
#         "accountId": "anonymous",
#         "apiId": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "domainName": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "domainPrefix": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "http": {
#             "method": "POST",
#             "path": "/generate",
#             "protocol": "HTTP/1.1",
#             "sourceIp": "103.39.129.223",
#             "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
#         },
#         "requestId": "f9288db4-8c32-423f-848f-a126ca633b4c",
#         "routeKey": "$default",
#         "stage": "$default",
#         "time": "26/Jun/2024:11:14:55 +0000",
#         "timeEpoch": 1719400495866
#     },
#     "body": "{\"modelName\":\"gpt-4-latest\",\"questionInfo\":{\"question\":\"Write an essay. Agree or Disagree: Many people in Japan are becoming more concerned about the environment. Use two of the points below to support your answer.\\n\\nCars\\nShopping Bags\\nEnvironment friendly appliances\\n\\nStructure:\\nIntro\\nBody\\nConclusion\\n\\nWord Count: 120 to 150\",\"rubrics\":[{\"rubricId\":\"8ebb346f-8e77-4c6b-a2ad-8d5a297367bc\",\"score\":5,\"criteria\":\"Able to write sentences about everyday topics and convey information, feelings, etc. using basic words\"},{\"rubricId\":\"640229e5-eca6-4859-8bdb-5547e8b69ff6\",\"score\":5,\"criteria\":\"Able to write detailed sentences on social topics using a variety of words and phrases to convey information and one's own thoughts while considering how to develop the content.\"},{\"rubricId\":\"e6454857-05f3-41ac-a5f2-28ec8d29bfa7\",\"score\":5,\"criteria\":\"Able to write detailed sentences on social topics, clearly explaining information, one's own thoughts, etc., using a variety of words and phrases, and clearly explaining developments, arguments, and reasons according to purpose\"}],\"maxScore\":\"15\",\"studentAnswerUrl\":\"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/667bf658cc5a74515a6707d8/13c80a56-fcd2-4c4c-9db2-3c530f221abd/ans_crop/01978dff-a92c-42d1-a707-a71a589d1f9e.webp\",\"studentAnswer\":\"Some people say that many people in Japan are becoming more concerned about the environment. I agree with this statement because of shopping bags and cars. First. many people in Japan taking shopping bags when they go shopping. This is because we have to pay money to use shopping bags in a lot of stores since 2020. So I always take shopping bags when I go shopping. I forget bring shopping bag sometimes. But my mother tells me to bring shopping bag. Second - some people use eco cars. This is because eco cars are good to protect environment. But eco cars are more expensive than oil cars. So some people doesn't buy eco cars. In conclusion, many people in Japan bring them shopping bags when they go shopping. Also, some people use eco car. Therefore, I think many people in Japan are becoming more concerned about the environment. (eco car is eco-friendly car.)\"},\"gradingPrompt\":\"default\"}",
#     "isBase64Encoded": False
# }
#     event = {
#     "version": "2.0",
#     "routeKey": "$default",
#     "rawPath": "/generate",
#     "rawQueryString": "",
#     "headers": {
#         "sec-fetch-mode": "cors",
#         "referer": "https://dev.smartpaperapp.com/",
#         "content-length": "2273",
#         "x-amzn-tls-version": "TLSv1.3",
#         "sec-fetch-site": "cross-site",
#         "x-forwarded-proto": "https",
#         "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
#         "origin": "https://dev.smartpaperapp.com",
#         "x-forwarded-port": "443",
#         "x-forwarded-for": "43.241.194.146",
#         "pragma": "no-cache",
#         "accept": "application/json, text/plain, */*",
#         "x-amzn-tls-cipher-suite": "TLS_AES_128_GCM_SHA256",
#         "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
#         "x-amzn-trace-id": "Root=1-668686bd-6d431b5506221a145b420c2f",
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": "\"Linux\"",
#         "host": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "content-type": "application/json",
#         "cache-control": "no-cache",
#         "accept-encoding": "gzip, deflate, br, zstd",
#         "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
#         "sec-fetch-dest": "empty"
#     },
#     "requestContext": {
#         "accountId": "anonymous",
#         "apiId": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "domainName": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "domainPrefix": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "http": {
#             "method": "POST",
#             "path": "/generate",
#             "protocol": "HTTP/1.1",
#             "sourceIp": "43.241.194.146",
#             "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
#         },
#         "requestId": "676804e7-a388-4f53-bc50-3353449b2c79",
#         "routeKey": "$default",
#         "stage": "$default",
#         "time": "04/Jul/2024:11:25:49 +0000",
#         "timeEpoch": 1720092349880
#     },
#     "body": "{\"modelName\":\"gpt-4-latest\",\"gradingPrompt\":\"essay\",\"questionInfo\":{\"question\":\"\",\"rubrics\":[{\"rubricId\":\"9b8d81aa-aeab-47ca-afb7-3de9ec8a563b\",\"score\":1,\"criteria\":\"Word Count (100+ / 120+ overall priority level will depend on whether Eiken 2 or pre-1)\"},{\"rubricId\":\"e7e32279-486f-468d-8fa2-717d6d02dac6\",\"score\":1,\"criteria\":\"Uses transition words or phrases to connect ideas\"},{\"rubricId\":\"7ebf5d5c-85de-48ed-9ec9-81af6499b69c\",\"score\":1,\"criteria\":\"clear opinion stated\"},{\"rubricId\":\"c264a834-2c93-4eaa-8a0b-4b2ea3b7cf8b\",\"score\":1,\"criteria\":\"supported with facts/reasons\"},{\"rubricId\":\"d8ca99e7-f68b-4f6f-abf6-c53b9493d040\",\"score\":1,\"criteria\":\"good vocabulary usage on topic (synonyms and antonyms, vocabulary from Monoxer)\"},{\"rubricId\":\"f7837f0e-bb28-451d-a642-94e28d4b8621\",\"score\":1,\"criteria\":\"uses subject sentence, transitions between topics, transitions between topics and conclusion effectively\"},{\"rubricId\":\"a9670768-7dab-4aa0-80e8-4c5d3afce838\",\"score\":1,\"criteria\":\"demonstrates correct use of an adverb (necessary at the pre-1 level)\"},{\"rubricId\":\"aab94de0-eccb-4756-95a2-d448d22488c4\",\"score\":1,\"criteria\":\"conclusion rephrases the main points made in body paragraph 1 and 2\"}],\"maxScore\":\"8\",\"studentAnswer\":\"Some people says people should continue to work after the retirement age. I agree this topic. I have three reasons . First, people are worried about health of older people. But now, healthcare is developing. So they have to earn money to go to hospital. Second, older people needs a lot of money. Forex example, shopping, use their hobbies, and buying daily necessities. If an old people lives alone, he or she has to earn more by himself or herself . Lastly, some people get stressed out when they are working. But some older people bet stressdout when they doesn't work. Because older people have worked for a long time. In conclusion, older people have to earn money after the retirement age. Because they need a lot of money for a living. So I agree with people should continue to work after the retirement age . [ 144 words ]\",\"studentAnswerUrl\":[\"https://smartpaper-ai-service-crops.s3.ap-south-1.amazonaws.com/dev/6686788a8ff12f73fe3532f4/aa5aa258-a0fc-4540-9f33-ca255460d498/ans_crop/e9fbd853-ccdd-47b9-bce8-ea39ca02ca2a.webp\"]}}",
#     "isBase64Encoded": False
# }
#     event = {
#     "version": "2.0",
#     "routeKey": "$default",
#     "rawPath": "/generate",
#     "rawQueryString": "",
#     "headers": {
#         "content-length": "854",
#         "x-amzn-tls-version": "TLSv1.3",
#         "x-forwarded-proto": "https",
#         "postman-token": "60b74cd2-365d-4465-854b-db779e44693d",
#         "x-forwarded-port": "443",
#         "x-forwarded-for": "43.241.194.146",
#         "accept": "*/*",
#         "x-amzn-tls-cipher-suite": "TLS_AES_128_GCM_SHA256",
#         "x-amzn-trace-id": "Root=1-6687fa88-4e60c86152785555224a57bf",
#         "host": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "content-type": "application/json",
#         "cache-control": "no-cache",
#         "accept-encoding": "gzip, deflate, br",
#         "user-agent": "PostmanRuntime/7.37.3"
#     },
#     "requestContext": {
#         "accountId": "anonymous",
#         "apiId": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "domainName": "4oxnsyrln7iziosrtbsx2atmd40xgvgw.lambda-url.ap-south-1.on.aws",
#         "domainPrefix": "4oxnsyrln7iziosrtbsx2atmd40xgvgw",
#         "http": {
#             "method": "POST",
#             "path": "/generate",
#             "protocol": "HTTP/1.1",
#             "sourceIp": "43.241.194.146",
#             "userAgent": "PostmanRuntime/7.37.3"
#         },
#         "requestId": "52f1b213-f380-4553-800e-1e148a92480b",
#         "routeKey": "$default",
#         "stage": "$default",
#         "time": "05/Jul/2024:13:52:08 +0000",
#         "timeEpoch": 1720187528547
#     },
#     "body": "{\n    \"modelName\": \"gpt-4-latest\",\n    \"questionInfo\": {\n        \"question\": \"In cold countries, a solution of water and ethylene glycol is used as a coolant in automobile engine radiators. Explain why.\",\n        \"rubrics\": [\n            {\n                \"rubricId\": \"d2c00f3a-aa02-4f89-9ca3-1273be98c2d1\",\n                \"score\": 0.5,\n                \"criteria\": \"The reason should be mentioned as: The addition of ethylene glycol depresses the freezing point of water.\"\n            },\n            {\n                \"rubricId\": \"8fcbeb2e-e9f4-4513-9046-3465e450e22a\",\n                \"score\": 0.5,\n                \"criteria\": \"The explanation should be: Water freezes at lower temperature\"\n            }\n        ],\n        \"maxScore\": 1,\n        \"studentAnswerUrl\": [\n          \"\" ],\n        \"studentAnswer\": \"\"\n    },\n    \"gradingPrompt\": \"default\"\n}",
#     "isBase64Encoded": False
# }


    event = {}
    context = {}
    result = message_handler(event=event, context=context)
    if (os.environ['cloudWatch'] == "True"):
        print(result)
