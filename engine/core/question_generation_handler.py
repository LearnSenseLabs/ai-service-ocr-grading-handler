import json
import logging
import os,re
from typing import List, Dict, Any
from nanoid import generate
import anthropic
from openai import OpenAI
import requests

from engine.gen_utils_files.database_calling import get_user_metadata_from_mongo, updated_userDB_monogo

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
ANTHROPIC_API_KEY = os.getenv('claude_api_key')
if not ANTHROPIC_API_KEY:
    raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set")

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def extract_grade_number(grade_level: str) -> int:
    """
    Extract the numeric grade level from a string.
    
    Args:
        grade_level (str): The grade level string (e.g., 'grade1', 'grade10')
    
    Returns:
        int: The numeric grade level
    
    Raises:
        ValueError: If the grade level cannot be extracted
    """
    match = re.search(r'\d+', grade_level)
    if match:
        return int(match.group())
    else:
        return grade_level
    raise ValueError(f"Unable to extract grade number from '{grade_level}'")

def calculate_age_range(grade_number: str) -> str:
    """
    Calculate the age range based on the grade level.
    
    Args:
        grade_level (str): The grade level string (e.g., 'grade1', 'grade10')
    
    Returns:
        str: The calculated age range
    """
    # grade_number = extract_grade_number(grade_level)
    lower_age = grade_number + 5
    upper_age = grade_number + 8
    return f"{lower_age}-{upper_age}"

def question_generation(input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate questions using Claude AI based on the given input data.

    Args:
        input_data (Dict[str, Any]): A dictionary containing input parameters.
        system_prompt (str): The system prompt to guide Claude's behavior.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing generated questions and answers.

    Raises:
        ValueError: If input parameters are invalid.
        anthropic.APIError: If there's an error with the Anthropic API.
        json.JSONDecodeError: If the response cannot be parsed as JSON.
        Exception: For any other unexpected errors.
    """
    try:
        # Extract relevant information from input_data
        # grade_level = extract_grade_number(input_data.get('gradeLevel'))
        grade_level = input_data.get('gradeLevel')
        subject = input_data.get('subject')
        education_board = input_data.get('educationBoard')
        topic = input_data.get('topic')
        num_questions = input_data.get('numberOfQuestions', 5)
        content_types = input_data.get('contentType', ['mcq', 'openEnded'])
        content_types_str_value = ', '.join(['Multiple choice question' if item == 'mcq' else item for item in content_types])

        age_range = calculate_age_range(grade_level) if(isinstance(grade_level,int)) else "18-22"
        
        # Validate input
        if not all([grade_level, subject, education_board, topic]):
            raise ValueError("Missing required input parameters")
        if num_questions < 2:
            raise ValueError("Number of questions must be at least 2")

        # Construct the prompt
        # user_prompt = (f"Generate {num_questions} questions about {topic} for {grade_level} {subject} "
        #                f"according to the {education_board} board. ")
        
        ##### generated for gpt-40 on nov 12 2024.... #### 
        # user_prompt = f"Generate {num_questions} questions on the topic '{topic}' for grade-{grade_level} students studying {subject} under the {education_board} curriculum. Only include {content_types_str_value} questions. Provide in purely JSON format and no other."
        
        ### removed education board from the prompt
        user_prompt = f"Generate {num_questions} questions on the topic '{topic}' for grade-{grade_level} students studying {subject}. Only include {content_types_str_value} questions. Provide in purely JSON format and no other."
        
        generation_format = f""
        system_prompt = (
        f"You are a teacher creating a set of questions for grade-{grade_level} students."
        f"The questions should cover a variety of topics relevant to the syllabus and should be appropriate for {age_range} year old students. "
        f"Requirements: "
        f"Variety of Topics: Ensure that the questions cover all major topics from the grade {grade_level}-{subject} syllabus, including given topics of {topic}. "
        f"Difficulty Level: The questions should be appropriately challenging for grade-{grade_level} students, balancing between conceptual understanding and practical application. "
        f"Clarity and Simplicity: Use simple language and clear instructions, making sure each question is easy to understand for {age_range} year-old students. "
        f"Engagement: Where possible, make the questions interesting and engaging by incorporating real-life scenarios, experiments, or fun elements to stimulate curiosity and interest in the subject. "
        f"Useable Formats: Only include {content_types_str_value} questions."
        f"Options Generation: Generate four options for multiple-choice questions in JSON format {{'opt1':'option1', 'opt2':'option2', 'opt3':'option3', 'opt4':'option4'}}. For short answer questions, leave the options as an empty list {{[]}} and provide the actual answer in the Answer field. "
        f"For MCQs, the Answer field should always contain the correct option identifier (e.g., opt2 for the second option)."
        f"Rubric generation: Generate a detailed rubric for the following question based on the provided topic, skill, question type, and marks. The rubric should be specific, concise, and divided into categories according to the total marks available. Provide one clear and specific line that describes what is required to earn that score. Ensure the rubric covers all key aspects of the answer, including accuracy, completeness, and understanding of the concept, do not generate rubrics for multiple-choice questions just give {{[]}}. Give me in this form, and do not provide a 0 mark rubric text. Based on the provided image, create rubrics for the given question and its associated marks. Distribute the total marks into specific criteria (e.g., if a question is worth 2 marks, assign 1 mark for one step and 1 mark for another, or 0.5 increments for multiple smaller steps). The rubric should be structured as JSON objects with the following structure: {{'RubricText': Text of the rubrics, 'Marks': marks awarded for following these particular rubrics in multiple of 0.5}} "
        f"Format: Provide the questions in JSON format with keys: Grade, Subject, Topic, Question, questionType, Marks, Answer, Rubrics, options. "
        #f"ASCII Format: For mathematical expressions, formulas, and fractions, provide them in plain ASCII format using symbols such as '/' for fractions, '^' for exponents, and 'sqrt(...)' for square roots. For Fractions use (numerator)/(denominator)"
        f"ASCII Format: For mathematical expressions, formulas, and fractions, enclose all mathematical terms in backticks (` `). Use symbols such as `/` for fractions, `^` for exponents, and `sqrt(...)` for square roots. For fractions, write as `(numerator)/(denominator)`, don't give ascii format in options text in mcq. "
        f"Only provide questions in ASCII format and not in Latex format. Represent vectors using component notation, e.g., `a = (1)i + (-3)j + (1)k`. Do not use LaTeX-like formatting such as `\\` or `\\hat`."
        f"Ensure that all mathematical terms such as `cos(theta)`, `sin(theta)`, `tan(30 degrees)`, and similar are enclosed entirely within backticks."
        f"Ensure that all the mathematical terms in all the fields Question, Answer, Rubrics and options strictly follow this format and are in backticks (` `)."
        f"Limit the set to {num_questions} questions, covering the topics comprehensively."
        f"Only include {content_types_str_value} questions."
    )
        
        ##### older version till dec-4 ###########
    #     system_prompt = (
    #     f"You are a teacher creating a set of questions for grade-{grade_level} students."
    #     f"The questions should cover a variety of topics relevant to the syllabus and should be appropriate for {age_range} year old students. "
    #     f"Requirements: "
    #     f"Variety of Topics: Ensure that the questions cover all major topics from the grade {grade_level}-{subject} syllabus, including given topics of {topic}. "
    #     f"Difficulty Level: The questions should be appropriately challenging for grade-{grade_level} students, balancing between conceptual understanding and practical application. "
    #     f"Clarity and Simplicity: Use simple language and clear instructions, making sure each question is easy to understand for {age_range} year-old students. "
    #     f"Engagement: Where possible, make the questions interesting and engaging by incorporating real-life scenarios, experiments, or fun elements to stimulate curiosity and interest in the subject. "
    #     f"Useable Formats: Only include {content_types_str_value} questions."
    #     f"Options Generation: Generate four options for multiple-choice questions in JSON format {{'opt1':'option1', 'opt2':'option2', 'opt3':'option3', 'opt4':'option4'}}. For short answer questions, leave the options as an empty list {{[]}} and provide the actual answer in the Answer field. "
    #     f"For MCQs, the Answer field should always contain the correct option identifier (e.g., opt2 for the second option)."
    #     f"Rubric generation: Generate a detailed rubric for the following question based on the provided topic, skill, question type, and marks. The rubric should be specific, concise, and divided into categories according to the total marks available. Provide one clear and specific line that describes what is required to earn that score. Ensure the rubric covers all key aspects of the answer, including accuracy, completeness, and understanding of the concept, do not generate rubrics for multiple-choice questions just give {{[]}}. Give me in this form, and do not provide a 0 mark rubric text. Based on the provided image, create rubrics for the given question and its associated marks. Distribute the total marks into specific criteria (e.g., if a question is worth 2 marks, assign 1 mark for one step and 1 mark for another, or 0.5 increments for multiple smaller steps). The rubric should be structured as JSON objects with the following structure: {{'RubricText': Text of the rubrics, 'Marks': marks awarded for following these particular rubrics in multiple of 0.5}} "
    #     f"Format: Provide the questions in JSON format with keys: Grade, Subject, Topic, Question, questionType, Marks, Answer, Rubrics, options. "
    #     #f"ASCII Format: For mathematical expressions, formulas, and fractions, provide them in plain ASCII format using symbols such as '/' for fractions, '^' for exponents, and 'sqrt(...)' for square roots. For Fractions use (numerator)/(denominator)"
    #     f"ASCII Format: For mathematical expressions, formulas, and fractions, enclose **all** mathematical terms in backticks (` `). Use symbols such as `/` for fractions, `^` for exponents, and `sqrt(...)` for square roots. For fractions, write as `(numerator)/(denominator)`, don't give ascii format in options text in mcq. "
    #     f"Ensure that all mathematical terms such as `cos(theta)`, `sin(theta)`, `tan(30 degrees)`, and similar are enclosed entirely within backticks."
    #     f"Ensure that all the mathematical terms in all the fields Question, Answer, Rubrics and options are in backticks (` `)."
    #     f"Limit the set to {num_questions} questions, covering the topics comprehensively."
    #     f"Only include {content_types_str_value} questions."
    # )

        #### for claude 3.5 on nov 12 2024... ####
        # system_prompt = (f"You are a teacher creating a set of questions for grade-{grade_level} students based on the {education_board} curriculum. The questions should cover a variety of topics relevant to the syllabus and should be appropriate for {age_range} year old students."
        #                 f"Requirements: "
        #                 f"Variety of Topics: Ensure that the questions cover all major topics from the grade {grade_level}-{subject} syllabus, including given topics of {topic}."                         
        #                 f"Difficulty Level: The questions should be appropriately challenging for grade-{grade_level} students, balancing between conceptual understanding and practical application. Clarity and Simplicity: Use simple language and clear instructions, making sure each question is easy to understand for {age_range} year-old students."
        #                 f"Engagement: Where possible, make the questions interesting and engaging by incorporating real-life scenarios, experiments, or fun elements to stimulate curiosity and interest in the subject."                        
        #                 # f"Useabl Formats: Include a mix of multiple-choice questions with four options and short answer questions."
        #                 f"Useable Formats: Give only this type: {content_types_str_value} of the questions while generating while generating questions."
        #                 f"options generation: Generate four options for multiple-choice questions, make each option different from others, in this JSON format:{{'opt1':'option-1', 'opt2':'option2', 'opt3':'option3', 'opt4':'option4'}}, in case of short answer give option field as {{[]}}."
        #                 f"Rubric generation: Generate a detailed rubric for the following question based on the provided topic, skill, question type, and marks. The rubric should be specific, concise, and divided into categories according to the total marks available. provide one clear and specific line that describes what is required to earn that score. Ensure the rubric covers all key aspects of the answer, including accuracy, completeness, and understanding of the concept, do not generate rubrics for multiple-choice questions just give {{[]}}, give me in this form, and do not provide a 0 mark rubric text. Based on the provided image, create rubrics for the given science question and its associated marks. The rubric should be structured as JSON objects with the following structure: {{'RubricText': Text of the rubrics, 'Marks': marks awarded for following these particular rubrics in multiple of 0.5}} "
        #                 f"Ensure the rubrics align closely with the skill and topic presented in the image. The rubric should be precise, specific to the question, and not overly detailed."                                                                        
        #                 f"Format: Provide the questions in a JSON format with the following keys: Grade, Subject, Topic, Question, questionType, Marks, Answer, Rubrics, options."
        #                 f"Make sure the set does not contain more than {5} questions, covering all the listed topics comprehensively.")

        # Call Claude API
        # response = client.messages.create(
        #     model="claude-3-5-sonnet-20240620",
        #     system=system_prompt,
        #     messages=[
        #         {
        #             "role":"user",
        #             "content":[
        #                 {
        #                     "text": user_prompt,
        #                     "type": "text"
        #                 }
        #             ]
        #         }
        #     ],
        #     max_tokens=2500,
        #     temperature=0
        # )

        # # Parse the response
        # content = response.content[0].text
        
        # # Extract JSON content
        # json_match = re.search(r'\[.*\]', content, re.DOTALL)
        # if not json_match:
        #     raise ValueError("No JSON content found in Claude's response")
        
        # json_content = json_match.group()
        
        #### GPT API Calling
        messages = [{
            "role":"system",
            "content":system_prompt
        },{
            "role":"user",
            "content":user_prompt
        }]
        
        if(len(messages)>0):    
            # API_KEY = os.getenv("OPENAI_API_KEY")
            # API_ENDPOINT = "https://api.openai.com/v1/chat/completions"

            # headers = {
            #     "Content-Type": "application/json",
            #     "Authorization": f"Bearer {API_KEY}",
            # }

            # data = {
            #     "model": "gpt-4o",
            #     "messages": messages,
            #     "response_format": {"type": "json_object"},
                # "temperature": 2,
                # "top_p":0.9,
                # "max_tokens":2500,
            #     # "frequency_penalty":frequency_penalty
            # }
            # # if max_tokens is not None:
            # #     data["max_tokens"] = 2500
            # # print("data going to gpt: ",json.dumps(data))
            
            # response = requests.post(API_ENDPOINT,headers=headers, data=json.dumps(data))
            # print(response)
            # if response.status_code == 200:
            #     response = response.json()
            #     # print("output: ",response)
            #     questions = json.loads(response["choices"][0]["message"]["content"])
            
            ############# new implementation with pydantic and json parsing ###########
            from pydantic import BaseModel
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            class Rubric(BaseModel):
                rubricText: str
                marks: int

            class Option(BaseModel):
                opt1: str
                opt2: str
                opt3: str
                opt4: str

            class QuestionMetaData(BaseModel):
                grade: int
                subject: str
                topic: str
                question: str
                questionType: str
                marks: int
                answer: str
                rubrics: List[Rubric]
                options: List[Option]

            class QuestionsResponse(BaseModel):
                questions: List[QuestionMetaData]

            # Modify the completion request
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=messages,
                response_format=QuestionsResponse, 
                temperature= 2,
                top_p=0.9,
                max_tokens=2500,
            )
            try:
                questions_response = completion.choices[0].message.parsed.dict()
                # print(questions_response)
                # for question in questions_response.questions:
                    # print(question.dict())  # Print each question in JSON format
            except Exception as e:
                print(f"Error: {e}")
        
        # questions = json.loads(json_content)

        # Validate the response structure
        # if not isinstance(questions, list):
        #     raise ValueError("Unexpected response format from Claude")

        # for question in questions:
        #     if not all(key in question for key in ['Question', 'Answer']):
        #         raise ValueError("Question or answer missing in Claude's response")

        logger.info(f"Successfully generated {len(questions_response)} questions about {topic}")
        return questions_response

    except ValueError as ve:
        logger.error(f"Invalid input: {str(ve)}")
        raise

    except anthropic.APIError as ae:
        logger.error(f"Anthropic API error: {str(ae)}")
        raise

    except json.JSONDecodeError as je:
        logger.error(f"Failed to parse Claude's response as JSON: {str(je)}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error in question generation: {str(e)}")
        raise
    
def convert_question_format(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert the questions from Claude's format to the desired output format.

    Args:
        questions (List[Dict[str, Any]]): The list of questions generated by Claude.

    Returns:
        List[Dict[str, Any]]: The list of questions in the desired format.
    """
    converted_questions = []
    if(isinstance(questions,dict)):
        if(questions.__contains__('questions')):
            questions = questions['questions']
    for que_wise_data in questions:
        new_que_wise_data = {
            "questionText": que_wise_data["question"],
            "marks": int(que_wise_data["marks"]),
            "ans": [que_wise_data["answer"]],
            "instructions": '',
            "showInstructions": True,
            "lineSpacing": 20,
            "lineColor": '#828282',
            "aiGrading": True,
            "size": '1/8',
            "questionId": generate(),
            "answerBoxId": generate(), 
            "settings": 4,
            # "markUpFormat":"asciiMath"
        }
        try:
            if(que_wise_data.__contains__('Question Type')):
                generated_question_type = que_wise_data["Question Type"].lower()
            elif(que_wise_data.__contains__('QuestionType')):
                generated_question_type = que_wise_data["QuestionType"].lower()
            elif(que_wise_data.__contains__('questionType')):
                generated_question_type = que_wise_data["questionType"].lower()
            else:
                generated_question_type = ''
                
            if( (generated_question_type == "mcq")
               or(generated_question_type == "multipleChoice") or (generated_question_type == "multiplechoice")
               or (generated_question_type == "multiple choice")
               or (generated_question_type=="multiple choice question")
               or (generated_question_type=="Multiple Choice")):
                new_que_wise_data["contentSubType"] = "multipleChoice"
                new_que_wise_data["contentSubSubType"] = "tickmark"
                
                option_index = 0
                new_que_wise_data["options"] = []
                new_que_wise_data['markUpFormat'] = 'text'
                # for options_data in q['options']:
                for key, value in que_wise_data['options'][0].items():
                    # correct_option_index = 0
                    if(value == que_wise_data["answer"]):
                        correct_option_index = option_index
                    elif(key==que_wise_data["answer"]):
                        correct_option_index = option_index
                    # new_que_wise_data["options"].append({
                    #     "value": value,
                    #     "correctOption":correct_option_index,
                    #     "optionId": generate()
                    # })
                    option_index +=1
                
                for key, value in que_wise_data['options'][0].items():
                    
                    new_que_wise_data["options"].append({
                        "value": value,
                        "correctOption":str(correct_option_index),
                        "optionId": generate()
                    })
                
                new_que_wise_data['rubrics'] = que_wise_data['rubrics']
                new_que_wise_data["ans"] = que_wise_data["answer"]
            else:
                new_que_wise_data['rubrics'] = []
                new_que_wise_data['markUpFormat'] = 'asciiMath'
                for rubrics_data in que_wise_data['rubrics']:
                    new_que_wise_data["rubrics"].append({
                        "score": rubrics_data['marks'],
                        "criteria": rubrics_data['rubricText'],
                        "rubricId": generate()
                    })
                
                new_que_wise_data["contentSubType"] = "openEnded"
                new_que_wise_data["contentSubSubType"] = "shortAnswer"

            converted_questions.append(new_que_wise_data)
        except Exception as e:
            logger.error(f"Error in converting question format: {str(e)}")
            raise
        

    return converted_questions

    # questions_json = [{'Grade': '1', 'Subject': 'Mathematics', 'Topic': 'Addition', 'Question': 'What is 5 + 3?', 'Question Type': 'Multiple Choice', 'Marks': 1, 'Answer': '8', 'Rubrics': [...], 'options': {...}}, {'Grade': '1', 'Subject': 'Mathematics', 'Topic': 'Addition', 'Question': 'Riya has 4 apples. Her mother gives her 2 more apples. How many apples does Riya have now?', 'Question Type': 'Short Answer', 'Marks': 2, 'Answer': '6 apples', 'Rubrics': [...], 'options': [...]}, {'Grade': '1', 'Subject': 'Mathematics', 'Topic': 'Addition', 'Question': 'Which of these is equal to 6 + 1?', 'Question Type': 'Multiple Choice', 'Marks': 1, 'Answer': '7', 'Rubrics': [...], 'options': {...}}, {'Grade': '1', 'Subject': 'Mathematics', 'Topic': 'Addition', 'Question': 'Fill in the blank: 3 + ___ = 8', 'Question Type': 'Short Answer', 'Marks': 2, 'Answer': '5', 'Rubrics': [...], 'options': [...]}, {'Grade': '1', 'Subject': 'Mathematics', 'Topic': 'Addition', 'Question': 'There are 7 birds on a tree. 2 more birds join them. How many birds are there on the tree now?', 'Question Type': 'Multiple Choice', 'Marks': 1, 'Answer': '9', 'Rubrics': [...], 'options': {...}}]
# with open('question.json', 'r') as file:
#     json_data = json.load(file)
# convert_question_format(questions=json_data)

def credit_reducer(user_id,generated_question_list):
    # number_of_credits_consumed =
    number_of_questions_generated = len(generated_question_list)
    user_data_list = get_user_metadata_from_mongo(user_id)
    
    if(len(user_data_list)>0):
        user_data = user_data_list[0]
        user_data['credits'] = user_data['credits'] - number_of_questions_generated/10
        updated_userDB_monogo(user_data)
        return f"question generated successfully, and updated credits to {user_data['credits']} from {user_data['credits'] + number_of_questions_generated/10}"