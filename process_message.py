import ollama


def process_message(message):
    with open("./prompt.md", "r") as file:
        file_content = file.read()
        prompt = file_content.replace("[INSERT USER MESSAGE HERE]", message)

    print(message)

    messages = [
        {"role": "user", "content": prompt},
    ]

    try:
        response = ollama.chat(model="qwen:4b", messages=messages)
        return int(response["message"]["content"])
    except:
        print("Error occurred in parser.")
        return 0
