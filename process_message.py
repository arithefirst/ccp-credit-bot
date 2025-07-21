import ollama


def process_message(message):
    with open("./prompt.md", "r") as file:
        file_content = file.read()
        prompt = file_content.replace("[INSERT USER MESSAGE HERE]", message)

    messages = [
        {"role": "user", "content": prompt},
    ]

    try:
        response = ollama.chat(model="qwen:4b", messages=messages)
        score = int(response["message"]["content"])
        return score, True  # Return success status along with score
    except Exception as e:
        print(f"Error occurred in parser: {e}")
        return 0, False  # Return failure status with default score
