import re

# Sample string
text = 'Some text here ocr:"B" and here ocr:\'C\' and more text. ``json { "ocr": "B" } ```'

# # Regex pattern
# pattern = r"(?i)ocr:\s*['\"](.*?)['\"]"

# # Find all matches
# matches = re.findall(pattern, text)

# # Prepare the output in the desired format
# # outputs = [{"ocr": match} for match in matches]
# outputs = [match for match in matches]

# print(outputs)

import re
import json

# Regex pattern for ocr:"value" and ocr:'value'
pattern_ocr = r"(?i)ocr:\s*['\"](.*?)['\"]"

# Regex pattern for JSON { "ocr": "value" }
pattern_json = r"(?i)\{\s*['\"]ocr['\"]\s*:\s*['\"](.*?)['\"]\s*\}"

# Find all matches for both patterns
matches_ocr = re.findall(pattern_ocr, text)
matches_json = re.findall(pattern_json, text)

# Combine the results
matches = matches_ocr + matches_json
print(matches)
# Prepare the output in the desired format
outputs = [{"ocr": match} for match in matches]

print(outputs)
