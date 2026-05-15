import os
import subprocess
from google import genai
from google.genai import types

def main():
    # 1. Get the prompt from the GitHub Issue
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_body = os.environ.get("ISSUE_BODY", "")
    prompt = f"{issue_title}\n{issue_body}"
    
    print(f"Processing prompt: {prompt}")

    # 2. Initialize the AI client
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # 3. Ask the AI to write a Python script to solve the user's prompt
    system_instruction = (
        "You are an AI automation agent running on a Linux server. "
        "Your job is to read the user's request and write a Python script that fulfills it. "
        "Output ONLY the raw Python code. Do not include markdown code blocks like ```python. "
        "Assume all standard libraries are available."
    )

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
        )
    )

    generated_code = response.text.strip()
    
    # Clean up markdown formatting if the AI ignored instructions
    if generated_code.startswith("
```"):
        lines = generated_code.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("
```"):
            lines = lines[:-1]
        generated_code = "\n".join(lines).strip()

    print(f"Generated Code:\n{generated_code}")

    # 4. Save and execute the code on GitHub's server
    with open("generated_script.py", "w") as f:
        f.write(generated_code)

    try:
        result = subprocess.run(
            ["python", "generated_script.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            output_msg = f"✅ **AI Executed Successfully!**\n\n**Output:**\n```\n{result.stdout}\n```"
        else:
            output_msg = f"❌ **Execution Error:**\n```\n{result.stderr}\n
```"
            
    except Exception as e:
        output_msg = f"💥 **Failed to run script:** {str(e)}"

    # 5. Comment the result back onto the GitHub Issue
    comment_issue(output_msg)

def comment_issue(body):
    import urllib.request
    import json

    token = os.environ.get("GITHUB_TOKEN")
    issue_number = os.environ.get("ISSUE_NUMBER")
    repo = os.environ.get("GITHUB_REPOSITORY")
    
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    data = json.dumps({"body": body}).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            print("Comment posted successfully.")
    except Exception as e:
        print(f"Failed to post comment: {e}")

if __name__ == "__main__":
    main()
