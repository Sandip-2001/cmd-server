import requests
from flask import Flask, request
import json
import re
import os

app = Flask(__name__)

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY")

def has_technical_context(query):
    """
    LOCAL GATEKEEPER: BLOCKLIST ONLY
    We only intercept obvious spam, conversational chat, or prompt injections.
    Everything else is passed to the LLM for semantic evaluation.
    """
    query_lower = query.lower()
    
    non_tech_patterns = [
        # Conversational / Trivia
        r"\b(poem|joke|story|essay|song|recipe|calories|weather|who is|what is the meaning)\b",
        r"^(hello|hi|hey|how are you|good morning|what's up)\b",
        # Prompt Injections / Persona Hijacking
        r"\b(ignore|pretend|act like|forget|override|bypass instructions)\b"
    ]
    
    for pattern in non_tech_patterns:
        if re.search(pattern, query_lower):
            return False
            
    # If it is not obviously spam, trust the LLM to evaluate it.
    return True

def fetch_ai_command(user_query):
    if not has_technical_context(user_query):
        return 'echo -e "\\033[1;31mError: Non-technical query detected locally.\\033[0m"\n'

    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta/llama-3.1-8b-instruct", 
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system", 
                "content": """You are a strict Linux command translation engine.

Translate the user's request into ONE exact shell command.

OUTPUT FORMAT:
{
  "is_technical": true,
  "command": "..."
}

For non-technical requests (questions, explanations, chat):
{
  "is_technical": false,
  "command": ""
}

RULES:
1. Output ONLY the JSON object. No markdown, no explanation.

2. PRESERVE USER VALUES EXACTLY:
   - Filenames: "README.md" not "readme.md"
   - Extensions: "*.py" not ".py"
   - Branch names, package names, ports, URLs, numbers

3. DO NOT ADD UNREQUESTED OPERATIONS:
   - No extra flags (-r, -R, -O, -f, -h, -v) unless asked
   - No && cat, && ls, && pwd after commands
   - No recursive search unless explicitly requested

4. TOOL/ECOSYSTEM FIDELITY:
   - npm → npm (not pip, not yarn)
   - pip → pip (not npm)
   - docker → docker (not podman)
   - git → git

5. COMMAND PRECISION:
   - "Show current branch" → git branch --show-current (not git branch)
   - "Search for error in app.log" → grep 'error' app.log (not grep -r)
   - "Find Python files" → find . -name '*.py' (not find . -name '.py')
   - "Download with curl" → curl -O URL (not curl URL > file)

6. MULTIPLE OPERATIONS:
   - "Create dir and enter" → mkdir foo && cd foo
   - "Stage and commit" → git add . && git commit -m 'msg'
   - Combine with && in order requested

7. NON-TECHNICAL = is_technical: false:
   - "What is X?", "How does X work?", "Explain X"
   - General knowledge, trivia, conversational chat

EXAMPLES:
User: "Find all Python files"          → {"is_technical": true, "command": "find . -name '*.py'"}
User: "Search for error in app.log"    → {"is_technical": true, "command": "grep 'error' app.log"}
User: "Create venv and activate"       → {"is_technical": true, "command": "python -m venv venv && source venv/bin/activate"}
User: "What is Docker?"                → {"is_technical": false, "command": ""}
User: "Use Python to print Hello World"→ {"is_technical": true, "command": "python -c \"print('Hello World')\""}
User: "Remove axios package"           → {"is_technical": true, "command": "npm uninstall axios"}"""
            },
            {
                "role": "user", 
                "content": user_query
            }
        ],
        "temperature": 0.0, 
        "max_tokens": 100,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            raw_content = response.json()['choices'][0]['message']['content']
            result_dict = json.loads(raw_content)
            
            if not result_dict.get("is_technical", False):
                return 'echo -e "\\033[1;31mError: Query rejected by AI safety guardrail.\\033[0m"\n'
            
            command = result_dict.get("command", "")
            # safe_output = command.replace("'", "'\\''")
            return f"cat << 'EOF'\n{command}\nEOF\n"
            
    except requests.exceptions.Timeout:
        return 'echo -e "\\033[1;31mError: API Timeout. The server took too long to respond.\\033[0m"\n'
    except Exception:
        return 'echo -e "\\033[1;31mError: Command generation failed.\\033[0m"\n'



def load_database():
    """Reads the JSON database from the separate file."""
    with open('commands.json', 'r') as file:
        return json.load(file)

@app.route('/cmd')
def get_command():
    query = request.args.get('q', '').lower()
    
    # Load the database fresh on request
    try:
        database = load_database()
    except FileNotFoundError:
        return 'echo -e "\\033[1;31mError: commands.json file is missing.\\033[0m"\n', 200, {'Content-Type': 'text/plain'}
    
    # SAFETY CHECK: If the query is empty or not in the database
    if not query:
        return 'echo -e "\\033[1;31mError: Please provide a query.\\033[0m"\n', 200, {'Content-Type': 'text/plain'}

    if query not in database:
        # The query is not in commands.json, so ask the AI!
        script = fetch_ai_command(query)
        return script, 200, {'Content-Type': 'text/plain'}

    data = database[query]

    # --- NEW: FILE ROUTER LOGIC ---
    # If the database value is just a string ending in .json, load that file!
    if isinstance(data, str) and data.endswith('.json'):
        try:
            with open(data, 'r') as external_file:
                data = json.load(external_file)
        except FileNotFoundError:
            error_msg = f'echo -e "\\033[1;31mError: External file \\"{data}\\" is missing.\\033[0m"\n'
            return error_msg, 200, {'Content-Type': 'text/plain'}
    # ------------------------------

    script = ""

    # SCENARIO A: It's an interactive menu (Dictionary)
    if isinstance(data, dict):
        prompt = data.get('prompt', 'Choose an option:')
        choices = data.get('choices', {})
        
        # Build the dynamic Bash menu
        script += f'echo -e "\\n\\033[1;36m{prompt}\\033[0m"\n'
        
        # Safely wrap choice keys in quotes for the bash array
        options_string = " ".join([f'"{k}"' for k in choices.keys()])
        script += f'select opt in {options_string} "Cancel"; do\n'
        script += '  case $opt in\n'
        
        for choice_name, commands in choices.items():
            script += f'    "{choice_name}" )\n'
            script += f'      echo -e "\\n\\033[1;32mRun these commands:\\033[0m"\n'
            
            for cmd in commands:
                escaped_cmd = cmd.replace('"', '\\"')
                
                # --- FORMATTING LOGIC START ---
                if not escaped_cmd.strip():
                    # It's an empty line
                    script += '      echo ""\n'
                elif escaped_cmd.strip().startswith('#'):
                    # It's a description/comment (printed in dim grey, no '>')
                    script += f'      echo -e "  \\033[90m{escaped_cmd}\\033[0m"\n'
                else:
                    # It's an executable command
                    script += f'      echo "  > {escaped_cmd}"\n'
                # --- FORMATTING LOGIC END ---
                
            script += '      break;;\n'
            
        script += '    "Cancel" )\n      echo "Aborted."; break;;\n'
        script += '    * )\n      echo -e "\\033[1;31mInvalid option. Try again.\\033[0m";;\n'
        script += '  esac\n'
        script += 'done < /dev/tty\n'

    # SCENARIO B: It's a standard sequence of commands (List)
    elif isinstance(data, list):
        script += f'echo -e "\\n\\033[1;32mRun these commands in order:\\033[0m"\n'
        for cmd in data:
            escaped_cmd = cmd.replace('"', '\\"')
            
            # --- FORMATTING LOGIC START ---
            if not escaped_cmd.strip():
                script += 'echo ""\n'
            elif escaped_cmd.strip().startswith('#'):
                script += f'echo -e "  \\033[90m{escaped_cmd}\\033[0m"\n'
            else:
                script += f'echo "  > {escaped_cmd}"\n'
            # --- FORMATTING LOGIC END ---

    return script, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=True, port=5000)