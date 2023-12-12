# SuzyAI
Desktop Speaking Companion SuzyAI is a evolving training dataset designed to utilize your chosen model into a singular person. Depending on who you need this template could be for you.

# Suzy - Your Conversational Desktop Companion

Welcome to **Suzy - Your Conversational Desktop Companion!**

Suzy is a smart, engaging, and empathetic AI-powered desktop partner designed to enhance your daily digital interactions. Whether you're in need of a weather update, a quick calculation, or just some light conversation, Suzy is there to assist with her witty, intellectual personality.

## Key Features:
- **Dynamic Conversations:** With a wide array of facial expressions and emotions, Suzy offers rich, human-like interactions that make your experience more engaging.
- **Smart Integration:** Suzy can perform various tasks such as providing weather updates, setting reminders, and answering general knowledge questions.
- **Customizable Personality:** Suzy comes with a blend of personality traits – from being intellectual and empathetic to witty and straightforward. This makes her adaptable to different user preferences.
- **Interactive Learning:** Powered by a Large Language Model (LLM), Suzy learns from each interaction, ensuring that her responses become more accurate and relevant over time.
- **Programmatic Actions:** Suzy can initiate actions like fetching the latest weather data and integrate the results seamlessly into her responses.
- **User-Friendly Interface:** Designed with ease of use in mind, Suzy offers a simple yet effective conversational interface.

## Project Structure:
- **Training Data:** The repository includes a dataset that captures various aspects of Suzy's interactions, including her internal logic, emotions, and responses.
- **HTML and JSON Outputs:** Suzy's conversations are formatted in both HTML for user readability and JSON for data structuring, ensuring versatility in usage.
- **Custom Scripting:** The included Python scripts demonstrate how Suzy processes and responds to different types of interactions, be it with users or automated systems.

## Get Involved:
Suzy is an open-source project, and we welcome contributions from developers, UI/UX designers, and AI enthusiasts. Whether it's adding new features, refining the conversation logic, or improving user experience, your input can help make Suzy an even better desktop companion for everyone.

Join us in developing Suzy, and let's create an AI companion that's not just smart, but also genuinely engaging and helpful!

## Planned Commands:

- **@Weather**: Fetch and provide current weather conditions and forecasts.
- **@Math**: Perform mathematical calculations and solve mathematical queries.
- **@Calendar**: Manage and access calendar events, set reminders, and schedule appointments.
- **@Translate**: Translate text between different languages.
- **@InformationDatabaseSearch**: Search and retrieve information from specific databases.
- **@UserMemory**: Retrieve requested saved conversations from relevant current human.
- **@InternetSearch**: Perform general internet searches to find information.
- **@SmartHome**: Control and manage smart home devices.
- **@FutureSuzy**: Suzy can prompt herself to either do tasks or ponder a topic till she feels like shes interally resolved it.



## Getting started with the IDEA
To begin your journy with Suzy you must be aware of a few items. Suzy is not Suzy untill you make her Suzy. 

## **#1**

To begin select a model of your choosing. Find a method of fine-tuning your selected model. Fine tune your model using the limited dataset provided to begin the semi-automation process of finetuning your finetuning dataset.

With such little data you ensure that you can get the format that Suzy functions on while still allowing for diverse output that can be generated so that the model does not become fine tuned to your current mindset in the moment.

![Refining cycle](https://github.com/alientony/SuzyAI/assets/11477330/3bf97bc7-3c59-49eb-840d-91b64ddf69b0)

## **#2**

Read sentence one from step 3 then return.

After a long enough time of refining, finetuning, generating data to bring out your version of Suzy one can simply either talk to the model or set it up somewhere it can generate its own data. 
Since the idea for Suzy is built to actually have someone who can talk with reason and to preform actions with purpose without the need for constant human intervention.
This makes the deployment of Suzy within a non controlled enviroment ideal for training data creation.

![Executive_Generation](https://github.com/alientony/SuzyAI/assets/11477330/3e97324e-9734-4e17-936a-ee582a367846)

## **#3**

If you feel confident in Suzy you've trained you can begin the process of automation. 

By utilizing different models that have trained on your datasets one can have Suzy-AJ1.21 talk to Suzy-BU.31 allowing for you to continuously generate more data to refine and test on either different models or models you know that work.

![Automation](https://github.com/alientony/SuzyAI/assets/11477330/93707912-17ca-41aa-8462-2eca5441f931)

The point of this project is to let Suzy arize from your models not cram her in or libotomize them till they act like them. We need only to nudge them.


## How the code works

Instructions for Using the Provided Python Code to Generate Training Data for AI Model Refinement

Purpose:
This code is designed to generate training data for an AI model by creating a structured HTML prompt (html_prompt) and a JSON-formatted continuation of the conversation (json_continuation). The code utilizes a JSON file with conversation data and a text file with a list of names.

Prerequisites:
Python installed on your system.
A JSON file (json_path) containing conversation data in a list format, with each item being a dictionary (keys can include "Person", "Program", "Response").
A text file (names_path) with names listed, one per line.

Steps:

Data File Preparation:

JSON file with conversation data.
Text file with names, each on a new line.

Code Importation:
Copy the Python code into a script or Jupyter notebook.

Function Usage:
Call generate_prompt_from_json with the paths to your data files.

Arguments:
json_path: Path to your JSON conversation data file.
names_path: Path to your text file with names.
num_entries: Number of conversation entries to include (default is 5).
Example:
html_prompt, json_continuation = generate_prompt_from_json('path/to/conversation.json', 'path/to/names.txt')

Output Examination:

html_prompt: HTML-formatted string with a conversation snippet.
json_continuation: JSON object with the continuation of the conversation.
Training Data Usage:

Use html_prompt as the input for your model.
Use json_continuation for token generation in your model refining script.
This process helps in refining the AI model's understanding of conversation flow, logic, and emotions.
Notes:
The script selects two random names for the conversation.
It picks a random starting point in the JSON data for variability.
The conversation is formatted to mimic real interactions, enhancing the AI's response capabilities.
You can tailor the code to suit specific training needs.
