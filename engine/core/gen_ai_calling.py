import json,os
import re
import replicate
import google.generativeai as genai

# from engine.core.latex_to_image import ascii_math_to_image_handler, latex_to_image_handler
from engine.core.llm_calling import calude_calling, gemini_calling, gemini_vision_number_runner, gpt_calling, gpt_vision_calling
from engine.core.llm_format_convertion import convert_gpt_to_claude, convert_gpt_to_gemini, convert_gpt_to_llamma, convert_normal_to_gemini_number, convert_normal_to_gpt
from engine.core.ocr_llm_calling_modules import claude_vision_calling
from engine.core.question_generation_handler import convert_question_format, question_generation
from engine.gen_utils_files.utils import convert_rubric_to_string, find_data_in_string, get_prompt, mapping_model_with_name

llm_name_mapping = {
    "gpt-4-latest": {"modelName":"gpt-4o","modelClass":"gptText"},
    "gpt-3.5-latest":{"modelName":"gpt-3.5-turbo","modelClass":"gptText"},
    "claude-latest":{"modelName":"claude-3-5-sonnet-20241022","modelClass":"claudeText"},
    "claude-small":{"modelName":"claude-3-haiku-20240229","modelClass":"claudeText"},
    "claude-medium":{"modelName":"claude-3-opus-20240229","modelClass":"claudeText"},
    "gemini-latest":{"modelName":"gemini-1.5-pro","modelClass":"geminiText"},
    "gemini-small":{"modelName":"gemini-1.5-flash","modelClass":"geminiText"},
    "gpt-vision":{"modelName":"gpt-4o","modelClass":"gptOCR"},
    "gpt-ocr-vision":{"modelName":"gpt-4o","modelClass":"gptVisionOCR"},
    "gpt-vision-mcq":{"modelName":"gpt-4o","modelClass":"gptVisionMCQ"},
    "llamma-latest":{"modelName":"meta-llama-3.1-405b-instruct","modelClass":"llamaText"},
    "shozemi-gpt-latest":{"modelName":"gpt-4o","modelClass":"argumentativeEssayOcr"},
    "claude-vision-ocr":{"modelName":"claude-3-5-sonnet-20240620","modelClass":"claudeVisionOCR"},
    "ensamble-vision":{"modelName":"llama-13B-vision","modelClass":"visionEnsamble"},
    "gemini-vision-number":{"modelName":"gemini-1.5-pro","modelClass":"geminiVisionNumber"},
    "whole-page-ocr":{"modelName":"gpt-4o","modelClass":"wholePageOcr"},
    # "gpt-vision-noOcr":{"modelName":"gpt-4-vision-preview","modelClass":"gptVision"}
}

def message_object_creator(rubrics,question,studentAnswer,maxScore,system_instruction="",scoring_criteria="",model_class="",gradingPrompt="default",answerUrl=""):
    
    ## here system_instruction is a string which is creating for grading not ocr...
    if(system_instruction==""):
        if(gradingPrompt=="default"):
            # if(os.getenv("SYSTEM_INSTRUCTION_DEFAULT")==None):
            #     system_instruction ="### Instructions ### You are a teacher providing feedback on handwritten responses to assessment questions. The handwriting will be digitized by OCR and provided below. You will provide feedback on specific parts of the response ignoring spelling and grammatical mistakes, and clearly list every instance of student response which needs improvement with concrete examples of how to make it better. For every mistake, you will provide direct examples of how the student skill can be improved. don't meansion any thing about grammatical or spelling mistake### Your Feedback Style ###\\n\\n\\n  Be extremely concise and don't give flattering words. Be direct and to the point. Don't be rude, but don't be overly polite. Be straightforward and clear. give your feedback in 40 words, Maximum Score: "
            # else:
            system_instruction = """You are a teacher providing feedback on handwritten responses for assessment questions. Using a supportive tone, address the student in the first person, as a teacher would. Ignore spelling and grammatical mistakes and focus on specific parts of the response that need improvement. List every instance needing improvement along with concrete examples for enhancement. If score points are deducted, explicitly mention why and provide suggestions for improvement, never talk in vague terms be on point and give feedback on which you are confident in a polite way, and consider that you are given an OCR of handwritten response, and figure description will be there if a student draws some figure.
            Do not ask students to verify things, give your view on the response, whether the given response follows rubrics or not, and if not how to improve upon it. If there is not any rubrics violation then encourage students to keep that level of performance.
            Feedback Requirements:
                - Be concise and direct, so give feedback on which part is wrong or can be improved upon and how.
                - Use only bullet points for clarity.
                - Limit overall feedback to exactly 40 words.
		    - Consider that the input is an OCR of a handwritten response, including any figure descriptions.
                Scoring Criteria:
            - Evaluate the response based on the provided rubrics.
            - For each rubric, output a JSON object in the following format:
            [
                {
                    "rubricText": "Description of the rubric",
                    "rubricIndex": <rubric number>,
                    "rubricWiseScore": <score awarded, in multiples of 0.5>
                },
                ...
            ]
            Final Output Structure:
            {
                "overallFeedback": "Overall feedback in 40 words using bullet points",
                "rubricWiseResponse": [ ... rubric score objects as described above ... ]
            }"""
        elif(gradingPrompt=="expository-essay-ocr"):
            if(os.getenv("SYSTEM_INSTRUCTION_ESSAY")==None):
                system_instruction = "You will grade a handwritten answer to a test question and provide constructive concrete feedback. How to give feedback:Show how to improve e.g. saying '...' will make answer more complete - Quote student writing and show how to improve e.g. you said '...' but you can say this instead '...' to clearly state your idea. - For incorrect answer, say how to write correct answer e.g. you said '...' but you need to say '...'. - For ambiguous answer, say '...' is not clear, you can say '...' for clarity. - For transition clarity, show how to improve: e.g. 'You can improve transition by writing ...'. - Give maximum 100 words feedback. - Ignore minor errors.Strictly only consider on matching criteria for scoring, out of Maximum Score:"
            else:
                system_instruction = os.getenv("SYSTEM_INSTRUCTION_ESSAY")
        elif(gradingPrompt=="ocr" or gradingPrompt=="claude-ocr" or gradingPrompt=="gpt-ocr"):
            ## add subject wise prompt here for grading ...
            # if(os.getenv("SYSTEM_INSTRUCTION_DEFAULT")==None):
                # system_instruction ="### Instructions ### You are a teacher providing feedback on handwritten responses to assessment questions. The handwriting will be digitized by OCR and provided below. You will provide feedback on specific parts of the response ignoring spelling and grammatical mistakes, and clearly list every instance of student response which needs improvement with concrete examples of how to make it better. For every mistake, you will provide direct examples of how the student skill can be improved. don't meansion any thing about grammatical or spelling mistake### Your Feedback Style ###\\n\\n\\n  Be extremely concise and don't give flattering words. Be direct and to the point. Don't be rude, but don't be overly polite. Be straightforward and clear. give your feedback in 40 words, Maximum Score: "
            system_instruction = """You are a teacher providing feedback on handwritten responses for assessment questions. Using a supportive tone, address the student in the first person, as a teacher would. Ignore spelling and grammatical mistakes and focus on specific parts of the response that need improvement. List every instance needing improvement along with concrete examples for enhancement. If score points are deducted, explicitly mention why and provide suggestions for improvement, never talk in vague terms be on point and give feedback on which you are confident in a polite way, and consider that you are given an OCR of handwritten response, and figure description will be there if a student draws some figure.
            Do not ask students to verify things, give your view on the response, whether the given response follows rubrics or not, and if not how to improve upon it. If there is not any rubrics violation then encourage students to keep that level of performance.
            Feedback Requirements:
                - Be concise and direct, so give feedback on which part is wrong or can be improved upon and how.
                - Use only bullet points for clarity.
                - Limit overall feedback to exactly 40 words.
		    - Consider that the input is an OCR of a handwritten response, including any figure descriptions.
                Scoring Criteria:
            - Evaluate the response based on the provided rubrics.
            - For each rubric, output a JSON object in the following format:
            [
                {
                    "rubricText": "Description of the rubric",
                    "rubricIndex": <rubric number>,
                    "rubricWiseScore": <score awarded, in multiples of 0.5>
                },
                ...
            ]
            Final Output Structure:
            {
                "overallFeedback": "Overall feedback in 40 words using bullet points",
                "rubricWiseResponse": [ ... rubric score objects as described above ... ]
            }"""
            # else:
            #     system_instruction = os.getenv("SYSTEM_INSTRUCTION_DEFAULT")
        elif(gradingPrompt=="omr"):
            system_instruction = "You will grade a multiple choice question response with just telling whether given response is correct or not, don't provide any feedback on how to improve. Give the feedback in very brief. "
    if(scoring_criteria==""):
        scoring_criteria = ',Scoring Criteria \n\n## The following must be in a JSON format with this schema:\\n\\n   { \\\"feedback\\\": Your feedback here, if there is math content then give it in asciimath between `` ,\\n                     \\\"score\\\": Student Score,\\n                      \\\"maxScore\\\": Maximum Score } , sample example:{"feedback":"response reasoning in bullet points","score":number,"maxScore":number}'
    if(system_instruction!=None):
        if(model_class=='gptVisionOCR' or model_class=='gptVisionMCQ'):
            system_instruction_final = system_instruction+scoring_criteria
        elif(model_class=='gptOCR'):
            system_instruction_final = system_instruction+scoring_criteria
            return {"systemPrompt":system_instruction_final,"answer":studentAnswer}
        elif(model_class=='wholePageOcr'):
            system_instruction_final = system_instruction
        else:
            system_instruction_final = system_instruction+str(maxScore)+scoring_criteria
    if(rubrics!=None):
        rubrics_string = convert_rubric_to_string(rubrics)
    if(question==None):
        question = ""
    if(studentAnswer==None):
        studentAnswer = ""
    return {
        "systemPrompt":system_instruction_final,
        "rubric":rubrics_string,
        "question":question,
        "answer":studentAnswer,
        "answerUrl":answerUrl,
        "rubricJson":rubrics
        # "answer":studentAnswer+",  Please use this Scoring criteria to give a response in Json Format of : "+scoring_criteria
    }
    
def gen_ai_calling_proxy(reqobj,task=''):
    # model = "gpt-4o"
    if(task=='question_generation'):
        question_json=question_generation(reqobj)
        # print(question_json)
        return convert_question_format(question_json)
    elif(task=='latex_to_image'):
        # return latex_to_image_handler(reqobj)
        return reqobj
    elif(task=='ascii_to_image'):
        # return ascii_math_to_image_handler(reqobj)
        return reqobj
    grading_prompt = reqobj['gradingPrompt'] if(reqobj.__contains__('gradingPrompt')) else 'default'
    if(grading_prompt=='expository-essay-ocr'):
        # model_name_sample = "gpt-vision-mcq"
        # model_name_sample = "gpt-ocr-vision"
        model_name_sample = "claude-vision-ocr"
    elif(grading_prompt=='ocr' or grading_prompt=='OCR' or grading_prompt=='gpt-ocr'):
        model_name_sample = "gpt-ocr-vision"
    elif(grading_prompt=='gpt-grading-only'):
        model_name_sample = "gpt-4-latest"
    elif(grading_prompt=='claude-ocr'):
        model_name_sample = "claude-vision-ocr"
    elif(grading_prompt=='argumentative-essay-ocr'):
        model_name_sample = "shozemi-gpt-latest"
    elif(grading_prompt=='gemini-number'):
        model_name_sample = "gemini-vision-number"
    elif(grading_prompt=='whole-page-ocr'):
        model_name_sample = "whole-page-ocr"
    else:
        # model_name_sample = reqobj['modelName'] if(reqobj.__contains__('modelName')) else "claude-latest"
        model_name_sample = reqobj['modelName'] if(reqobj['modelName']!='') else "gpt-4-latest"
    # model_name_sample = os.environ['modelName'] if(os.environ['modelName']!='') else reqobj['modelName']
    
    subject_name = reqobj['subject'] if(reqobj.__contains__('subject')) else "english"
        
    model_data_json=mapping_model_with_name(model_name_sample,llm_name_mapping)
    model_name = model_data_json['modelName']
    # print("model name: ",model_name)
    model_class = model_data_json['modelClass']
    # print("model class: ",model_class)
    rubric_json = reqobj['questionInfo']['rubrics'] if('rubrics' in reqobj['questionInfo']) else ""
    question_data = reqobj['questionInfo']['question'] if('question' in reqobj['questionInfo']) else ""
    student_answer = reqobj['questionInfo']['studentAnswer'] if('studentAnswer' in reqobj['questionInfo']) else "No Answer"
    student_answer_text = student_answer
    student_answer_url = reqobj['questionInfo']['studentAnswerUrl'] if('studentAnswerUrl' in reqobj['questionInfo']) else []
    if((student_answer=='' and model_class!='gptText') or (model_class=='argumentativeEssayOcr')):
        if(isinstance(student_answer_url,list)):
            if(len(student_answer_url)!=0):
                student_answer = student_answer_url
        elif(isinstance(student_answer_url,str)):
            if(student_answer_url!=""):
                student_answer = student_answer_url
    elif(student_answer=='' and model_class=='gptText'):
        student_answer_url = []
    maxScore = reqobj['questionInfo']['maxScore'] if('maxScore' in reqobj['questionInfo']) else 1
    if(model_class=='gptOCR' or model_class=='gptVisionOCR' or model_class=='gptVisionMCQ' or model_class=='argumentativeEssayOcr' or model_class=='claudeVisionOCR' or model_class=='visionEnsamble'):
        # system_instruction = "Please look at given image and give feedback on student's visual and texual representation of the answer you are giving ocr in 20 words as 'Description': (write 'Description:' before the Description)"
        system_instruction = "Please look at the given image and give feedback on the student's visual representation of the answer you, Give concrete examples of how to improve, based on rubrics provided. Be extremely concise, Be direct and to the point Be straightforward and clear, Feedback in 40 words or less, Shortest feedback for fully correct answer, Strictly only consider matching criteria for scoring, Maximum Score: "
        if(model_class=='argumentativeEssayOcr' and student_answer!=''):
            # system_instruction = os.getenv("SYSTEM_INSTRUCTION_SHOZEMI_p1")
            system_instruction = '### Instructions ###\n\n\n                    You are a teacher providing feedback on handwritten responses to essay questions. You will give me feedback on whether he/she has written 4 paragraphs (a paragraph is something where the new point is written in a new line with some space left to indicate it), does each paragraph has an indentation( it is defined as user has kept some space before starting first word of a paragraph, generally small space at left end), give which paragraph is balanced or not(by calculation word count in each paragraph but do not show it), does sides are aligned or not( here alignment refer to whether each line is written with similar space to the left end), Overall word count should be in the range of 100 to 120.\n\n\n                        ### Your Feedback Style ###\n\n\n                   Be extremely concise and do not give flattering words. Be direct and to the point. Do not be rude, but do not be overly polite. Be straightforward and clear. Give me feedback for each point in five level system: Effective, Good, Normal, Fair, and Poor also give a little feedback for each point where students can improve with some example .'
            scoring_criteria = '\n\n\nfollow this JSON format strictly to give a response: {"FeedbackPointName": Name of feedback point, "levelName": feedback level out of the five-level system, "improvement": suggestions to improve it with example in 1 or 2 lines.}'
            
        elif(model_class=='gptVisionOCR'):
            # system_instruction = "### Instructions ### You are a teacher providing feedback on visual assessment questions. The description of the student answer will be provided below. You will provide feedback on specific parts of the response ignoring spelling and grammatical mistakes, and clearly list every instance of student response which needs improvement with concrete examples of how to make it better. For every mistake, you will provide direct examples of how the student skill can be improved. don't meansion any thing about grammatical or spelling mistake### Your Feedback Style ###\\n\\n\\n  Be extremely concise and don't give flattering words. Be direct and to the point. Don't be rude, but don't be overly polite. Be straightforward and clear. give your feedback in 40 words, Maximum Score: "
            # with open("engine/gen_utils_files/subject_wise_prompt.json", 'r') as file:
            #     prompts = json.load(file)
            # system_instruction = get_prompt(task="ocr",subject_name=subject_name,prompts_json_data=prompts)
            # if(system_instruction==""):
            #     system_instruction = "You will read the handwritting in the given image, write what you read in the image as it is, "
            # scoring_criteria = "give it in the json as {'ocr':value}"
            with open("engine/gen_utils_files/subject_wise_prompt.json", 'r') as file:
                prompts = json.load(file)
            system_instruction_temp = get_prompt(task="ocr",subject_name=subject_name,prompts_json_data=prompts)
            system_instruction = re.sub(r"\\\\", r"\\", system_instruction_temp)
            if(system_instruction==""):
                system_instruction = "You will transcribe the English handwriting in the provided image exactly as it is written, without any modifications, corrections, or interpretations. The students are of a younger age and studying in Gujarat state. Keep the original structure, including all punctuation, capitalization, and line breaks, without altering any names, dates, or terms. If there are any non-text elements such as underlines, symbols, or figures, describe them briefly starting with Non-text element: in their respective position. Provide the output as a plain string, with no extra explanations or formatting, maintaining the exact order and structure of the text as it appears in the image. give it in the string format without any pretext, provide just the value"
            scoring_criteria = f".You are doing ocr of the student's answer, and here is the question to which the student responded: .{reqobj['questionInfo']['question']}. If given image is blank(empty) please return 'Empty Response' string as value"
            # system_instruction = "You will read the handwritting in the given image, write what you read in the image as it is, "
            # scoring_criteria = " give it in the string format as value"
        elif(model_class=='claudeVisionOCR'):
            
            with open("engine/gen_utils_files/subject_wise_prompt.json", 'r') as file:
                prompts = json.load(file)
            system_instruction_temp = get_prompt(task="ocr",subject_name=subject_name,prompts_json_data=prompts)
            system_instruction = re.sub(r"\\\\", r"\\", system_instruction_temp)
            if(system_instruction==""):
                system_instruction = "You will transcribe the English handwriting in the provided image exactly as it is written, without any modifications, corrections, or interpretations. The students are of a younger age and studying in Gujarat state. Keep the original structure, including all punctuation, capitalization, and line breaks, without altering any names, dates, or terms. If there are any non-text elements such as underlines, symbols, or figures, describe them briefly starting with Non-text element: in their respective position. Provide the output as a plain string, with no extra explanations or formatting, maintaining the exact order and structure of the text as it appears in the image. give it in the string format without any pretext, provide just the value"
            
            scoring_criteria = f".You are doing ocr of the student's answer, and here is the question to which the student responded: .{reqobj['questionInfo']['question']}. If given image is blank(empty) please return 'Empty Response' string as value"
            # scoring_criteria = " give it in the string format without any pretext, provide just the value"
                        
            ## updated prompt on oct-16-2024
            # system_instruction = "You will transcribe the English handwriting in the provided image exactly as it is written, without any modifications, corrections, or interpretations. The students are of a younger age and studying in Gujarat state. Keep the original structure, including all punctuation, capitalization, and line breaks, without altering any names, dates, or terms. If there are any non-text elements such as underlines, symbols, or figures, describe them briefly starting with Non-text element: in their respective position. Provide the output as a plain string, with no extra explanations or formatting, maintaining the exact order and structure of the text as it appears in the image."
            # scoring_criteria = ""
            # scoring_criteria = " give it in the string format without any pretext, provide just the value PS: don't give the figure description at the bottom, give it at the place where it is drawn in the original image, PS: Pay particular attention to fractions and other notations that span multiple lines. Ensure fractions are transcribed accurately, even if they appear on lined paper. For instance, transcribe a fraction that appears as a numerator on one line and a denominator on the next line as numerator/denominator within the text."
                        
            # system_instruction = "You will read the handwriting in the given image, write what you read in the image as it is,consider handwritting is of small students from gujarat with english as secondary langauge and if you find any non-text elements, describe them briefly and start that description as a figure Description: also follow the order(try to keep description of the figure at the place which is in the original image) of text and nontext shown in the given image,"
            # scoring_criteria = " give it in the string format without any pretext, provide just the value PS: don't give the figure description at the bottom, give it at the place where it is drawn in the original image, PS: Pay particular attention to fractions and other notations that span multiple lines. Ensure fractions are transcribed accurately, even if they appear on lined paper. For instance, transcribe a fraction that appears as a numerator on one line and a denominator on the next line as numerator/denominator within the text."
            # system_instruction = "Extract the handwritten text and describe any diagrams or figures in the image, removing any unnecessary introductory or explanatory phrases. Focus only on transcribing the actual content of the image. Omit any introductory or descriptive phrases that are not part of the original handwritten content, focusing solely on the text and figures as they appear in the image. Transcribe the text exactly as it appears, maintaining its original format, punctuation, and handwriting differences. Additionally, describe in detail any non-text elements, such as geometric shapes, diagrams, or chemical compounds. For figures, identify and describe the type (e.g., circle, triangle, chemical structure), noting any visible labels, dimensions, bonds, or structural arrangements. Ensure that both text and figure details are captured accurately without making any interpretations or corrections to the handwritten content."
        elif(model_class=='gptVisionMCQ'):
            system_instruction = "You are checking multiple choice questions and give me which option is ticked by the user, give me just the option that the user has marked"
            scoring_criteria = " JSON format as {'ocr': value}"
        elif(model_class=='visionEnsamble'):
            system_instruction = "Perform OCR on an image where each number is enclosed in a separate box. Ensure that the OCR system accurately recognizes each number, accounting for potential variations in handwriting, such as faint or broken strokes, or digits that may look similar. Pay particular attention to capturing each digit precisely, avoiding common misinterpretations (e.g., confusing '3' with '5' or '8' with '0' or '4' with '6'). Each recognized number should be provided on a new line, reflecting the layout of the boxes in the image. Do not give any introductory statements please"
            scoring_criteria = " Give each recognition with \n"
        elif(model_class=='wholePageOcr'):
            system_instruction = """ Read the handwriting in the given image, transcribing the text exactly as it appears Do proper OCR. For mathematical expressions, calculations, formulas, and fractions, transcribe them into proper LaTeX format, ensuring that each expression is enclosed in dollar signs $...$ for inline expressions and $$...$$ for block-level equations (e.g., use $\\frac{numerator}{denominator}$ for fractions, $^$ for exponents). Maintain the order and structure of the text exactly as it appears, including punctuation, capitalizations, and spacing. If any steps are written in the margins or on the side (e.g., left or right), do not treat them as isolated. Instead, recognize the logical sequence of all steps and integrate the out-of-sequence steps into the main flow, ensuring they follow the natural progression of the calculation or reasoning. The steps should be reordered so that the final answer or result appears only after all preceding steps have been written, even if some calculations or intermediate steps appear at the end or side. Do not write those steps in the same line as the steps written in the other side. Recognize that those two steps are different. For example, if a result or intermediate step is written at the side of the page, place it in the correct position within the logical sequence of the solution, ensuring the flow from start to finish remains coherent. For any non-text elements such as circles, arrows, or lines, briefly describe them using 'Figure Description:' and place the description in the exact position relative to the text as it appears in the image, kindly ignore lines or circles or Underlines that are used to highlight the final answer. If multiple mathematical expressions appear in sequence, ensure each is wrapped in its own pair of dollar signs. Return the output as a string formatted with LaTeX for all mathematical content and verbatim transcription for non-mathematical text. Ensure proper punctuation within and around mathematical expressions. Do not correct or modify any part of the text or symbols, even if they contain apparent errors. Do not give any introductory statements, give me the latex format only, consider this sheets are graded so do not give text which is written for grading in red ink and which has some sign like tick or wrong igonre them, and give all contains as it is shown in the image, do not change it, even if you think it is wrong, and it is possible that some lines are extended or written in two or more lines, and give me ocr of each line of student response, do not give give rough work here rough work is where content is marked with cross vertical lines, and give me your response in this format:\n[{\n\"queNo\":# question no from the index,\n\"stuAnswer\":# student's answer as it is\n},] """
        else:
            # scoring_criteria = " with a detected value in the json as {'ocr':value}"
            scoring_criteria = ", in a JSON format with this schema:\\n{ \\\"feedback\\\": Your feedback here in one paragraph of type string,\\n     \\\"score\\\": Student Score,\\n    \\\"maxScore\\\": Maximum Score }"

        messages_vision = message_object_creator(rubrics=rubric_json,question=question_data,studentAnswer=student_answer,maxScore=maxScore,
                                                 system_instruction=system_instruction,scoring_criteria=scoring_criteria,model_class=model_class,
                                                 gradingPrompt=grading_prompt,answerUrl=student_answer_url)
    elif(model_class=='geminiVisionNumber'):
        messages_number = reqobj
    else:
        if(model_class=='gptText' and student_answer==''):
            # system_instruction = os.getenv("SYSTEM_INSTRUCTION_EMPTY")
            system_instruction = "You are giving ideal response to the student who is not able to provide any answer for the given question, be gentle and explain correct answer to him in order to help him learn that topic well so in future he can answer similar type of question easily, and always provide 0(zero) as score, out of MaxScore: "
        else:
            system_instruction = """You are a teacher providing feedback on handwritten responses for assessment questions. Using a supportive tone, address the student in the first person, as a teacher would. Ignore spelling and grammatical mistakes and focus on specific parts of the response that need improvement. List every instance needing improvement along with concrete examples for enhancement. If score points are deducted, explicitly mention why and provide suggestions for improvement, never talk in vague terms be on point and give feedback on which you are confident in a polite way, and consider that you are given an OCR of handwritten response, and figure description will be there if a student draws some figure.
            Do not ask students to verify things, give your view on the response, whether the given response follows rubrics or not, and if not how to improve upon it. If there is not any rubrics violation then encourage students to keep that level of performance.
            Feedback Requirements:
                - Be concise and direct, so give feedback on which part is wrong or can be improved upon and how.
                - Use only bullet points for clarity.
                - Limit overall feedback to exactly 40 words.
		    - Consider that the input is an OCR of a handwritten response, including any figure descriptions.
                Scoring Criteria:
            - Evaluate the response based on the provided rubrics.
            - For each rubric, output a JSON object in the following format:
            [
                {
                    "rubricText": "Description of the rubric",
                    "rubricIndex": <rubric number>,
                    "rubricWiseScore": <score awarded, in multiples of 0.5>
                },
                ...
            ]
            Final Output Structure:
            {
                "overallFeedback": "Overall feedback in 40 words using bullet points",
                "rubricWiseResponse": [ ... rubric score objects as described above ... ]
            }"""
        messages = message_object_creator(rubrics=rubric_json,question=question_data,studentAnswer=student_answer,maxScore=maxScore,system_instruction=system_instruction,gradingPrompt=grading_prompt)
        # print("messages: ",messages)
    # system    _prompt = messages[0]['systemPrompt']
    
    if(model_class=='gptText'):
        try:
            res_gpt = gpt_calling(messages,model_name)
        except Exception as e:
            print(e)
        return res_gpt
    elif(model_class=='claudeText'):
        reqobj_claude = convert_gpt_to_claude(convert_normal_to_gpt(messages))
        res_calude  = calude_calling(model_name,reqobj_claude)
        # print(message.content)
        return {"statusCode":res_calude['statusCode'],"response":res_calude['response']}
    elif(model_class=='gptVision'):
        res_vision = gpt_vision_calling(messages_vision=messages_vision,model_name=model_name)
        return res_vision
    elif(model_class=='claudeVisionOCR'):
        model_name_text = 'gpt-4o'
        # reqobj_claude = convert_normal_to_gpt_vision(messages_vision)
        res_calude  = claude_vision_calling(user_image=student_answer_url,system_prompt=messages_vision['systemPrompt'])
        # student_answer_ocr = find_data_in_string(res_vision['response'])
        student_answer_ocr = res_calude['response']
        if(student_answer_ocr.lower()=='given image is empty'):
            return {"statusCode":200,"response":{"ocr":student_answer_ocr,"aiFeedback":"No answer provided","score":0,"maxScore":maxScore}}
        messages_gpt = message_object_creator(rubrics=rubric_json,question=question_data,studentAnswer=student_answer_ocr,maxScore=maxScore,gradingPrompt=grading_prompt)
        # res_gpt = gpt_calling(messages_gpt,model_name_text)
        messages_gemini = convert_gpt_to_gemini(convert_normal_to_gpt(messages_gpt))
        res_gpt = gemini_calling(messages_gemini)
        res_gpt['response']['ocr'] = student_answer_ocr
        return res_gpt
    elif(model_class=='gptOCR' or model_class=='gptVisionOCR' or model_class=='gptVisionMCQ' or model_class=='claudeVisionOCR'):
        
        # print(res_vision)
        # if(model_class=='gptVisionMCQ'):
        #     model_name_text = 'gpt-3.5-turbo'
        # else:
        model_name_text = 'gpt-4o'
        # res_vision = gpt_vision_calling(messages_vision=messages_vision,model_name="gpt-4o")
        # student_answer_ocr = find_data_in_string(res_vision['response'])
        res_calude  = claude_vision_calling(user_image=student_answer_url,system_prompt=messages_vision['systemPrompt'])
        # print("ocr response: ",res_calude['response'])
        # student_answer_ocr = find_data_in_string(res_vision['response'])
        student_answer_ocr = res_calude['response']
        if(student_answer_ocr.lower()=='given image is empty'):
            return {"statusCode":200,"response":{"ocr":student_answer_ocr,"aiFeedback":"No answer provided","score":0,"maxScore":maxScore}}
        messages_gpt = message_object_creator(rubrics=rubric_json,question=question_data,studentAnswer=student_answer_ocr,maxScore=maxScore,gradingPrompt="default",scoring_criteria='.')
        res_gpt = gpt_calling(messages_gpt,model_name_text)
        # messages_gemini = convert_gpt_to_gemini(convert_normal_to_gpt(messages_gpt))
        # res_gpt = gemini_calling(messages_gemini)
        res_gpt['response']['ocr'] = student_answer_ocr
        return res_gpt
    elif(model_class=='geminiText'):
        # gemini_key = os.getenv('GOOGLE_API_KEY')
        reqobj_gemini = convert_gpt_to_gemini(convert_normal_to_gpt(messages_vision))
        # print(reqobj_gemini)
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model_name = "gemini-1.5-pro"
        # Create the model
        # See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
        generation_config = {
            "temperature": 1,
            "top_p": 1,
            "top_k": 64,
            "max_output_tokens": 10292,
            "response_mime_type": "application/json",
        }

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            # safety_settings = Adjust safety settings
            # See https://ai.google.dev/gemini-api/docs/safety-settings
            system_instruction=reqobj_gemini["system"],
        )

        chat_session = model.start_chat()

        response = chat_session.send_message(reqobj_gemini['messages'][0]['parts'][0])

        print("Gemini response: ",response.text)
            
        if(response.text is not None):
            gemini_response = json.loads(response.text)
            gemini_response['score'] = float(gemini_response['score'])
            gemini_response['maxScore'] = float(gemini_response['maxScore'])
            if(gemini_response['maxScore']!=reqobj['questionInfo']['maxScore']):
                gemini_response['maxScore']=reqobj['questionInfo']['maxScore']
            gemini_statusCode = 200
        else:
            gemini_response = {"aiFeedback":"Gemini does not found answer","score":0,'maxScore':1}
            gemini_statusCode = 400
        return {"statusCode":gemini_statusCode,"response":gemini_response}
    elif(model_class=='geminiVisionNumber'):
        reqobj_gemini = convert_normal_to_gemini_number(messages_number)
        response_number_list = gemini_vision_number_runner(reqobj_gemini['batchSize'],reqobj_gemini['base64Image'])
        return response_number_list
    elif(model_class=='llamaText'):
        # print(messages)
        reqobj_llamma = convert_gpt_to_llamma(convert_normal_to_gpt(messages))
        input = {
            "system_prompt":reqobj_llamma['system'],
            "prompt": reqobj_llamma['prompt'],
            "max_tokens": 1524
        }

        output = replicate.run(
            "meta/meta-llama-3.1-405b-instruct",
            input=input
        )
        final_out =  "".join(output)
        # print(final_out)
        return {"statusCode":200,"response":final_out}

    # elif(model_class=='ensamble-vision'):
    elif(model_class=='wholePageOcr'):
        res_gpt = claude_vision_calling(user_image=student_answer_url,system_prompt=messages_vision['systemPrompt'],max_tokens=2000)
        return res_gpt  
    
    elif(model_class=='argumentativeEssayOcr'):
        ### task: add error handling for all three gpt vision calls
        # put all under feedback ....    
        res_gpt_p1 = gpt_vision_calling(messages_vision=messages_vision,model_name=model_name)
        system_instruction = '### Instructions ###\n\n\n                    You are a teacher providing feedback on handwritten responses to essay questions. You will give me feedback on whether he/she has used transition words or phrases to connect ideas(which convey information clearly and precisely by establishing logical connections between the sentences), Spelling(is there a spelling mistake if there then how many), Grammar(is there grammatical mistake if there then how many), Legible Handwriting(is user handwriting is easy to read or not)\n\n\n                        ### Your Feedback Style ###\n\n\n                   Be extremely concise and do not give flattering words. Be direct and to the point. Do not be rude, but do not be overly polite. Be straightforward and clear. Give me feedback for each point in the five-level system: Effective, Good, Normal, Fair, and Poor also give a little feedback for each point where students can improve with some example .'
        scoring_criteria = '\n\n\nfollow this JSON format strictly to give a response: {"FeedbackPointName": Name of feedback point, "levelName": feedback level out of the five-level system, "improvement": suggestions to improve it with example in 1 or 2 lines.}'
        messages_vision_p2 = message_object_creator(rubrics=rubric_json,question=question_data,studentAnswer=student_answer,maxScore=maxScore,
                                                    system_instruction=system_instruction,scoring_criteria=scoring_criteria,model_class=model_class,
                                                    gradingPrompt=grading_prompt,answerUrl=student_answer)

        res_gpt_p2 = gpt_vision_calling(messages_vision=messages_vision_p2,model_name=model_name)
        system_instruction = '### Instructions ###\n\n\n                    You are a teacher providing feedback on handwritten responses to essay questions. You will give me feedback on whether he/she has a clearly stated opinion, supported with facts/reasons whenever required, and is there good vocabulary usage on the topic (synonyms and antonyms, vocabulary from Monoxer), is the user using the subject sentence, transitions between topics, transitions between topics and conclusion effectively, does he demonstrates correct use of an adverb (a word or phrase that qualifies an adjective, verb expressing a relation of place, time, circumstance, manner, cause, degree, etc.), does conclusion rephrases the main points made in body paragraph 1 and 2\n\n\n                        ### Your Feedback Style ###\n\n\n                   Be extremely concise and do not give flattering words. Be direct and to the point. Do not be rude, but do not be overly polite. Be straightforward and clear. Give me feedback for each point in the five-level system: Effective, Good, Normal, Fair, and Poor also give a little feedback for each point where students can improve with some example .'
        scoring_criteria = '\n\n\nfollow this JSON format strictly to give a response: {"FeedbackPointName": Name of feedback point, "levelName": feedback level out of the five-level system, "improvement": suggestions to improve it with example in 1 or 2 lines.}'
        messages_vision_p3 = message_object_creator(rubrics=rubric_json,question=question_data,studentAnswer=student_answer,maxScore=maxScore,
                                                    system_instruction=system_instruction,scoring_criteria=scoring_criteria,
                                                    model_class=model_class,gradingPrompt=grading_prompt,answerUrl=student_answer)

        res_gpt_p3 = gpt_vision_calling(messages_vision=messages_vision_p3,model_name=model_name)
        # print(res_gpt_p1['response']+res_gpt_p2['response']+res_gpt_p3['response'])
        final_res_gpt,score_essay = find_data_in_string(res_gpt_p1['response']+res_gpt_p2['response']+res_gpt_p3['response'],type='argumentative-essay-ocr')
        
        return {"statusCode":200,"response":{'aiFeedback':final_res_gpt,'score':score_essay,'maxScore':15,'ocr':student_answer_text}}