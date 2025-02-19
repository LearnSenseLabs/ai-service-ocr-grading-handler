import cv2
import numpy as np
import requests
import anthropic
import os
import uuid
import boto3
import base64
from together import Together
from io import BytesIO

from engine.core.llm_calling import gemini_vision_number_runner
from engine.core.llm_format_convertion import convert_normal_to_gemini_number
from engine.gen_utils_files.utils import add_response_to_db

anthropic_client = anthropic.Anthropic(
    api_key=os.getenv("claude_api_key")
)

system_prompt = """OCR the numbers in each row in the given image
Each number is enclosed in a box
Give only numbers separated by newline( \n )"""

class NumberOCR:
    
    def __init__(self, s3_links):
        self.s3_links = s3_links
        self.images = self._download_and_process_images()
        self.stacked_image = self._create_stacked_image()
    
    def number_list_flattern(self,number_list):
        result = [int(item) if item else 0 for sublist in number_list for item in sublist]

        # Remove zeros if they are not part of the desired result
        result = [x for x in result if x != 0]

        return result
    
    def _download_image_from_s3(self, s3_link):
        try:
            # Download image from S3
            response = requests.get(s3_link)
            if response.status_code != 200:
                raise Exception(f"Failed to download image from {s3_link}")
            
            # Convert to numpy array
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                raise Exception(f"Failed to decode image from {s3_link}")
                
            return image
        except Exception as e:
            raise Exception(f"Error processing image from {s3_link}: {str(e)}")

    def _download_and_process_images(self):
        processed_images = []
        for s3_link in self.s3_links:
            image = self._download_image_from_s3(s3_link)
            processed_images.append(image)
        return processed_images

    def image_s3_uploads(self, user_id, image_data):
        s3 = boto3.client('s3',
                    aws_access_key_id=os.environ['USER_ACCESS_KEY_ID'],
                    aws_secret_access_key=os.environ['USER_SECRET_ACCESS_KEY'],
                    region_name="ap-south-1")
        
        s3_bucket_name = 'open-crops-smartpaper'
        file_name = str(uuid.uuid4())
        content_type = 'image/png'
        s3_key = 'dev'+ "/" + user_id + "/" + file_name +".png"
        response = s3.put_object(Body=image_data,
                               Bucket=s3_bucket_name,
                               Key=s3_key,
                               ACL='public-read',
                               ContentType=content_type)

        s3_url = f"https://{s3_bucket_name}.s3.ap-south-1.amazonaws.com/{s3_key}"
        return s3_url

    def _create_stacked_image(self):
        if not self.images:
            raise ValueError("No images to process")
            
        border_size = 5
        max_width = max(max(img.shape[1] for img in self.images) + 2 * border_size, 300)
        total_height = sum(img.shape[0] for img in self.images) + (len(self.images) - 1) * 10 + len(self.images) * 2 * border_size
        stacked_image = np.ones((total_height, max_width, 3), dtype=np.uint8) * 255

        current_y = 0
        for img in self.images:
            height, width = img.shape[:2]
            bordered_img = cv2.copyMakeBorder(img, border_size, border_size, border_size, border_size, cv2.BORDER_CONSTANT, value=[0, 0, 0])
            stacked_image[current_y:current_y + height + 2 * border_size, :width + 2 * border_size] = bordered_img
            current_y += height + 2 * border_size + 10

        return stacked_image

    def claude_runner(self,encoded_image_base64):
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system=system_prompt,
            messages=[
            {
                "role": "user",
                "content": [{
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": encoded_image_base64
                }
                }]
            }
            ]
        )

        if message.type != "message":
            raise Exception(f"API call failed with status code {message.status_code}")

        numbers = message.content[0].text.strip().split('\n')
        if len(numbers) != len(self.images):
            raise ValueError("The number of returned numbers does not match the number of input images")

        return numbers    
    
    def llama_runner(self,encoded_image_url):
        
        # client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        client = ''

        response = client.chat.completions.create(
            model="meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
            messages=[
                {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Perform OCR on an image where each number is enclosed in a separate box. Ensure that the OCR system accurately recognizes each number, accounting for potential variations in handwriting, such as faint or broken strokes, or digits that may look similar. Pay particular attention to capturing each digit precisely, avoiding common misinterpretations (e.g., confusing '3' with '5' or '8' with '0' or '4' with '6'). Each recognized number should be provided on a new line, reflecting the layout of the boxes in the image. Do not give any introductory statements please"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": encoded_image_url
                        }
                    }
                ]
            }
            ],
            max_tokens=512,
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>","<|eom_id|>"],
            stream=True
        )
        numbers = []
        for token in response:
            if hasattr(token, 'choices'):
                if(len(token.choices)>0 and token.choices[0].delta.content!=''):
                    # print(token.choices[0].delta.content.strip().split('\n'), end='', flush=True)
                    # if(len(token.choices[0].delta.content.strip().split('\n'))>1):
                    numbers.append(token.choices[0].delta.content.strip().split('\n'))
        return self.number_list_flattern(numbers)

    def run(self, model_name):
        if not self.images:
            raise ValueError("No images to process")
            
        _, encoded_image = cv2.imencode('.png', self.stacked_image)
        encoded_image_base64 = base64.b64encode(encoded_image).decode('utf-8')
        
        if model_name == 'claude':
            numbers = self.claude_runner(encoded_image_base64)
        elif model_name == 'llama':
            encoded_image_url = self.image_s3_uploads(str(uuid.uuid4()), encoded_image.tobytes())
            numbers = self.llama_runner(encoded_image_url)
        return numbers

def assign_number_to_list(number_list,ensamble_list):
    # if(len(ensamble_list)==len(number_list)):
    #     print("len of ensamble and number list is same")
        
    for question_data_index in range(0,len(ensamble_list)):
                
        if(int(ensamble_list[question_data_index]['questionInfo']['correctAnswer'])==number_list[question_data_index]):
            score = ensamble_list[question_data_index]['questionInfo']['maxScore']    
                
        number_feedback_json = {
            "statusCode":200,
            "response":{
                "ocr":number_list[question_data_index],
                "maxScore":ensamble_list[question_data_index]['questionInfo']['maxScore'],
                "score":score,
                "aiFeedback":''
            }
        }
        
        db_add_flag=add_response_to_db(number_feedback_json,ensamble_list[question_data_index])
    return db_add_flag
        
def predict_llm_number(number_list):
    
    ################ older implementation ################
    # number_crop_list = []
    # for number in number_list:
    #     # print(number)
    #     number_crop_list.append(number['questionInfo']['studentAnswerUrl'])
    # ocr = NumberOCR(number_crop_list)
    # pred_numbers_list = ocr.run(model_name='llama')
    # assign_number_to_list(number_list=pred_numbers_list,ensamble_list=number_list)
    # return {"statusCode":200}
    
    ################### new implementation ################
    print("gemini number list: ",number_list)
    reqobj_gemini = convert_normal_to_gemini_number(number_list)
    response_number_list = gemini_vision_number_runner(reqobj_gemini['batchSize'],reqobj_gemini['base64Image'])
    return response_number_list