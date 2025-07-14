import subprocess

def call_ollama(prompt):
    result = subprocess.run(
        ['ollama', 'run', 'llama3'],
        input=prompt.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.stderr:
        print("Error or logs from ollama:", result.stderr.decode())
    return result.stdout.decode()


def summarize_comments(file_path):
    with open(file_path, 'r') as f:
        comments = f.read()

    prompt = f"""You're a content strategist for a creator. Analyze these comments:
    {comments}
    
    Summarize 3 main viewer themes. Suggest 3 future content ideas based on this."""
    
    return call_ollama(prompt)

print(call_ollama("Hello, what is your name?"))
