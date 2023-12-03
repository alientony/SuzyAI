
import json
import random

def generate_prompt_from_json(json_path, names_path, num_entries=5):
    # Load the JSON data
    with open(json_path, 'r') as file:
        data = json.load(file)

    # Load names from the text file and randomly select two names
    with open(names_path, 'r') as file:
        names = file.readlines()
        names = [name.strip() for name in names if name.strip()]
        if len(names) < 2:
            raise ValueError("Names file should contain at least two names.")
        selected_names = random.sample(names, 2)

    # Select a random starting point in the dataset and get a continuous set of entries
    start_index = random.randint(0, max(0, len(data) - num_entries))
    selected_data = data[start_index:start_index + num_entries]
    
    # Begin creating the HTML prompt
    html_prompt = (
        "<div>\n"
        "    <h2>Name: Suzy</h2>\n"
        "    <p>Personality: Smart, Intellectual, Empathetic, Witty, Straightforward, Dry Humor</p>\n"
        "    <p>Facial Expressions <>: Happy, Sad, Angry, Surprised, Confused, Thoughtful, Excited, Scared, Disgusted, Tired, Drowsy, Skeptical, Curious, Nervous, Relieved, Proud, Embarrassed, Hopeful, Jealous, Bored, Impressed, Grateful, Overwhelmed, Playful, Serene, Anxious, Amused, Sympathetic, Frustrated, Inquisitive</p>\n"
        "</div>\n\n"
        "<div>\n"
        "    <h3>Previous Conversation:</h3>\n"
    )

    # Adding selected conversation data using the selected names and handling program responses
    for entry in selected_data:
        if "Person" in entry:
            person_statement = entry["Person"]
            html_prompt += f"    <p>{selected_names[0]}: \"{person_statement}\"</p>\n"
        elif "Program" in entry:
            html_prompt += f"    <p><Program Response></p>\n"
        suzy_response = entry["Response"]
        html_prompt += f"    <p>{selected_names[1]}: \"{suzy_response}\"</p>\n"
    
    html_prompt += "</div>\n"

    # Adding the continuation of conversation in JSON format for the last entry
    last_entry = selected_data[-1]
    json_continuation = {
        "Continuation of Conversation": {
            "Internal Logic for Suzy": last_entry.get("Internal Logic For Suzy", {}),
            "Emotions Selected": last_entry.get("Emotions", {}),
            "Suzy's Response": last_entry.get("Response", "")
        }
    }

    return html_prompt, json_continuation
