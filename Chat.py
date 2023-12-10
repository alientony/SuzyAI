import requests
import json
import subprocess
import re

def execute_command_from_response(response):
    # Regular expression to find commands like "@Command argument"
    command_pattern = r"@(\w+)(?:\s+(.*))?"
    match = re.search(command_pattern, response)
    if match:
        command, argument = match.groups()
        return run_python_script(command, argument)
    return None

def run_python_script(command, argument):
    script_name = f"{command.lower()}.py"
    # Construct the command to execute the script
    # Assuming scripts are in a folder named 'programs'
    exec_command = f"python programs/{script_name} {argument}"
    try:
        result = subprocess.check_output(exec_command, shell=True)
        return result.decode().strip()
    except subprocess.CalledProcessError as e:
        return f"Error executing {command}: {e}"

def get_current_speaker(speaker_file):
    try:
        with open(speaker_file, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return "User"  # Default name if the file is not found

def save_current_speaker(speaker_file, speaker_name):
    with open(speaker_file, 'w') as file:
        file.write(speaker_name)

def translate_llm_response_to_training_data(user_input, llm_response):
    # Extract information from the LLM response
    internal_logic = llm_response["Continuation of Conversation"]["Internal Logic for Suzy"]
    emotions = llm_response["Continuation of Conversation"]["Emotions Selected"]
    suzy_response = llm_response["Continuation of Conversation"]["Suzy's Response"]

    # Construct the training data entry
    training_data_entry = {
        "Person": user_input,
        "Internal Logic For Suzy": internal_logic,
        "Emotions": emotions,
        "Response": suzy_response
    }

    return training_data_entry

def append_to_training_data_file(training_data_file, new_data):
    try:
        with open(training_data_file, 'r') as file:
            existing_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    existing_data.append(new_data)

    with open(training_data_file, 'w') as file:
        json.dump(existing_data, file, indent=4)

def chat_with_suzy(user_input, conversation_history_file, input_source="user"):
    # API URL for the local OpenAI compatible endpoint
    url = "http://127.0.0.1:5000/v1/completions"

    headers = {
        "Content-Type": "application/json"
    }

    # Load conversation history from the file
    try:
        with open(conversation_history_file, "r") as file:
            conversation_history = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        conversation_history = []

    # Get the current speaker's name
    current_speaker = get_current_speaker(speaker_file)

    # Add the input to the conversation history based on the input source
    if input_source == "user":
        conversation_history.append({current_speaker: user_input})
    elif input_source == "program":
        conversation_history.append({"Program": user_input})

    # Keep only the last 20 messages
    if len(conversation_history) > 20:
        conversation_history = conversation_history[-20:]

    # Construct the complete HTML prompt for the API
    complete_html_prompt = (
        "<div>\n"
        "    <h2>Name: Suzy</h2>\n"
        "    <p>Personality: Smart, Intellectual, Empathetic, Witty, Straightforward, Dry Humor</p>\n"
        "    <p>Facial Expressions <>: Happy, Sad, Angry, Surprised, Confused, Thoughtful, Excited, Scared, Disgusted, Tired, Drowsy, Skeptical, Curious, Nervous, Relieved, Proud, Embarrassed, Hopeful, Jealous, Bored, Impressed, Grateful, Overwhelmed, Playful, Serene, Anxious, Amused, Sympathetic, Frustrated, Inquisitive, Neutral, Smug</p>\n"
        "    <p>Commands @: @Weather, @Math, @Calendar, @Translate, @InformationDatabaseSearch, @UserMemory, @InternetSearch, @SmartHome, @NewPersonName</p>\n"
        "    <p>Internal Logic: Context, Internal Thoughts, Reasoning, Step By Step, Comparative Analysis, Cause and Effect, Problem and Solution, Pro-Con Evaluation, Hypothetical Scenarios, Historical Analysis, Logical Deduction, Critical Analysis, Conceptual Exploration, Analogical Reasoning</p>\n"
        "    <div>\n"
        "        <h3>Previous Conversation:</h3>\n"
    )

    for entry in conversation_history:
        if "Suzy" in entry:
            complete_html_prompt += f"<p>Suzy's Response: \"{entry['Suzy']}\"</p>\n"
        elif "Program" in entry:
            complete_html_prompt += f"<p><Program Response></p>\n"
        else:  # Handle other users
            for key, value in entry.items():
                complete_html_prompt += f"<p>{key}: \"{value}\"</p>\n"

    complete_html_prompt += "    </div>\n</div>"

    # Send a POST request to the local API endpoint
    response = requests.post(url, headers=headers, json={
        "prompt": complete_html_prompt,
        "max_tokens": 500  # Adjust as needed
    })

    # Extract Suzy's response from the JSON output
    suzy_response_json = response.json()['choices'][0]['text'].strip()
    # Parse the JSON to extract just the response text
    suzy_response_data = json.loads("{" + suzy_response_json + "}")  # Ensure valid JSON format
    suzy_response = suzy_response_data["Continuation of Conversation"]["Suzy's Response"].strip("<>").split(">")[-1].strip()
    training_data_entry = translate_llm_response_to_training_data(user_input, suzy_response_data)

    training_data_file = "suzy_training_data.json"
    append_to_training_data_file(training_data_file, training_data_entry)


    # Update the conversation history with Suzy's response
    conversation_history.append({"Suzy": suzy_response})

    # Save the updated conversation history to the file
    with open(conversation_history_file, "w") as file:
        json.dump(conversation_history, file, indent=4)

    # Execute any command in Suzy's response
    command_output = execute_command_from_response(suzy_response)

    if command_output:
        # Update Suzy's response or handle the command output as needed
        # For example, append it to the conversation history
        chat_with_suzy(command_output, conversation_history_file, input_source="program")


    return suzy_response, conversation_history

# Example Usage
user_input = "Hello Suzy, how are you?"
conversation_history_file = "suzy_conversation_history.json"
speaker_file = "Current_speaker.txt"
suzy_response, updated_history = chat_with_suzy(user_input, conversation_history_file)
print("Suzy:", suzy_response)
