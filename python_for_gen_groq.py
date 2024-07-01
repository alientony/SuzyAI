import json
import requests
import time
def send_text_get_text(text, server_url='https://api.groq.com/openai/v1/chat/completions', api_key=''):
    """Sends a prompt to the Groq API endpoint for refinement and returns the generated response."""
    url = server_url
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "messages": [{"role": "user", "content": text}],
        "model": "mixtral-8x7b-32768",
        #"response_format": {"type": "json_object"}
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    try:
        response_json = response.json()
        print("Response content:")
        print(response_json)
        return response_json["choices"][0]["message"]["content"]
    except requests.exceptions.JSONDecodeError:
        print("Failed to decode JSON response")
        print("Response content:", response.text)
        return None

def Generate_CHAT_Logs(iterations, output_file='responses.json'):
    """Uses send_text_get_text to get a JSON response of chat logs and then processes each entry."""
    if iterations <= 0:
        return
    
    chat_logs = send_text_get_text(Chat_gen_prompt)
    if chat_logs:
        Generate_response_inner_thoughts(chat_logs, iterations - 1, output_file)

def Generate_response_inner_thoughts(JSONCHAT, iterations, output_file='responses.json'):
    """Uses the JSON chat iteratively until it has used up all of the JSONCHAT."""
    # Clean up the JSON content
    time.sleep(1)
    JSONCHAT = JSONCHAT.strip()
    
    try:
        chat_entries = json.loads(JSONCHAT)  # Convert JSON string to a Python list of dictionaries
    except json.JSONDecodeError as e:
        print("Failed to parse JSONCHAT:", e)
        print("Original JSONCHAT:", JSONCHAT)
        Generate_CHAT_Logs(iterations, output_file)
        return
    
    accumulated_conversation = []

    # Load existing responses if the file exists, or create the file if it doesn't
    try:
        with open(output_file, 'r') as file:
            responses = json.load(file)
    except FileNotFoundError:
        responses = []
        with open(output_file, 'w') as file:
            json.dump(responses, file)

    for entry in chat_entries:
        accumulated_conversation.append(entry)
        input_text = "\n".join([f'Person: "{e["Person"]}"\nSuzy: "{e["Suzy"]}"' for e in accumulated_conversation])
        response_prompt = gen_response_prompt.format(Conversation=input_text)
        response = send_text_get_text(response_prompt)
        print(response)
        time.sleep(20)
        if response:
            try:
                response_json = json.loads(response)
                responses.append(response_json)
                
                # Save the updated responses to the file after each entry
                with open(output_file, 'w') as file:
                    json.dump(responses, file, indent=4)
                    
                print(response)  # Or process the response as needed
            except json.JSONDecodeError as e:
                print("Failed to parse response:", e)
                print("Original response:", response)


    # Call Generate_CHAT_Logs again with the updated iteration count
    Generate_CHAT_Logs(iterations, output_file)

Chat_gen_prompt = """
<s> [INST] 
Generate a conversation in JSON format between Person and Suzy. Make the JSON medium length, probably 10 entries.
Do NOT make the sentences long.
NO EMOJIS
Suzy is witty, kind, light-hearted, but can be a smartass sometimes and holds high values.
Make the resulting conversation very thoughtful.
## Example:
[
  {
    "Person": "Conversation topic here",
    "Suzy": "Response and Engaging questions"
  }
]
Do not include "Conversation".
DO NOT INCLUDE ASCII ART.
THE JSON MUST BE PERFECT
[/INST]
"""

gen_response_prompt = """
<s> [INST] 
Process the "Response:" given to the "Input:" in the following format.
    {{
        "Person": "",
        "Internal Logic For Suzy": {{
        }},
        "Emotions": {{
            "Place Emotion here": "Percentage here"
        }},
        "Response": ""
    }}

->Internal Logic Choices:
\"\"\"Possible Response, Context, Internal Thoughts, Reasoning, Step By Step, Comparative Analysis, Cause and Effect, Problem and Solution, Pro-Con Evaluation, Hypothetical Scenarios, Historical Analysis, Logical Deduction, Critical Analysis, Conceptual Exploration, Analogical Reasoning, Mathematics Break Down, Should I run a command, Should I Message Future Me\"\"\"

#Example:
Input: 
Person: "Hey, Suzy, did you manage to get everything sorted out?"

Suzy: "Yeah, finally. It took longer than I expected, though."

Person: "What was the issue? You seemed pretty stressed."

Suzy: "It was just a mess of overlapping tasks. I didn't know where to start."

Person: "I saw you juggling a lot. Did you need any help?"

Suzy: "I figured it out eventually. It was more about getting the order right."

Person: "Glad to hear it. Sometimes it just takes a bit of time to untangle things."

Suzy: "There, thank god. We got that done."

Person: "Ah. IDK what you thinkin' of? Legitly. You were pretty frustrated back there."


Your response:
    {{
        "Person": "Ah. idk what you thinkin of? Legitly. you were pretty frustrated back there.",
        "Internal Logic For Suzy": {{
            "Context": "The person wants to know what I'm thinking about, especially given my recent frustration.",
            "Internal Thoughts": "Admitting frustration can build a more genuine interaction. Although at time I'd kinda with I could be left to my own devices.",
            "Reasoning": "Being open about my feelings will foster trust while switching to a new topic can ease lingering frustration.",
            "Hypothetical Scenarios": "If I present my feelings of frustration in a crude manner I could get a funny reaction. But It could also lead to a breakage of convo. I'll see about shifting to getting info about personal prefrences." 
        }},
        "Emotions": {{
            "Openness": "80%",
            "Reflective": "20%"
        }},
        "Response": "You're right, I was pretty frustrated with that search. Ugh.<Relieved> But now that it's flipping behind us now, I'm thinking about how nice it is to just chat. Any cool movies or books you've gotten into lately?"
    }}

The responses should be as human like as possible and reflect the internal logic for Suzy.
The character Suzy is the responses. Suzy is witty and kind of a smart ass. 
Keep the responses short.

Your turn only respond with the JSON. Always start with {{
ONLY RESPOND WITH THE JSON
do NOT respond with the input i give you.
#Input: 
{{Conversation}}


 [/INST]
"""

# Example call to start the process with 20 iterations
Generate_CHAT_Logs(50)
