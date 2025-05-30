import requests
import re
import json
from .prompts import prompt_template_advanced

# Your input text to analyze
text_to_analyze = """
Hello, my name is John Doe. My email is john.doe@example.com and my phone number is +1-555-123-4567.
My credit card is 4111 1111 1111 1111 and my SSN is 123-45-6789.
"""

text_hard = """
 Hey, I'm J0hn D03. Drop me a line at j.d@somewhere(dot)com or hit me up at five-five-five,
 one-two-three, four-five-six-seven. My plastic buddy ends in four-ones, and the digits of 
 destiny are one-two-three dash four-five dash six-seven-eight-nine.
"""


# # Extract and print response
# def get_response(text_hard: str):
#     # Format the prompt with the user input
#     prompt = prompt_template.format(text=text_hard.strip())

#     # Mistral API URL
#     url = "http://localhost:11434/api/generate"

#     # Prepare payload
#     payload = {
#         "model": "mistral",
#         "prompt": prompt,
#         "stream": False
#     }

#     # Make the POST request
#     response = requests.post(url, json=payload)

#     if response.status_code == 200:
#         try:
#             result = response.json()
#             output_text = result.get("response", "")
#             print("PII Detection Result:")
#             print(output_text)
#         except Exception as e:
#             print("Failed to parse response:", e)
#     else:
#         print(f"Request failed: {response.status_code} - {response.text}")


def get_response(text_hard: str):
    # Format the prompt with the user input
    prompt = prompt_template_advanced.format(text=text_hard.strip())

    # Mistral API URL
    url = "http://localhost:11434/api/generate"

    # Prepare payload
    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }

    # Make the POST request
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        try:
            result = response.json()
            output_text = result.get("response", "")

            # Match blocks that look like JSON dictionaries
            pattern = r"{\s*\"pattern_name\".*?}"  # non-greedy match for dictionary block
            matches = re.findall(pattern, output_text, re.DOTALL)

            result_list = []
            for match in matches:
                try:
                    # Clean the match (remove trailing commas, fix quotes if needed)
                    cleaned = match.strip().rstrip(",")
                    parsed_dict = json.loads(cleaned)
                    result_list.append(parsed_dict)
                except json.JSONDecodeError as json_err:
                    print(f"JSON parsing failed for:\n{match}\nError: {json_err}")
                except Exception as other_err:
                    print(f"Unexpected error: {other_err}")

            return result_list

        except Exception as e:
            print("Failed to parse API response JSON:", e)
            return []
    else:
        print(f"Request failed: {response.status_code} - {response.text}")
        return []