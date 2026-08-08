from flask import Flask, request
import json

app = Flask(__name__)

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
    if not query or query not in database:
        error_msg = f'echo -e "\\033[1;31mError: Tool \\"{query}\\" not found in your database.\\033[0m"\n'
        return error_msg, 200, {'Content-Type': 'text/plain'}

    data = database[query]
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
                # Escape internal quotes so they don't break the bash echo
                escaped_cmd = cmd.replace('"', '\\"')
                script += f'      echo "  > {escaped_cmd}"\n'
            script += '      break;;\n'
            
        script += '    "Cancel" )\n      echo "Aborted."; break;;\n'
        script += '    * )\n      echo -e "\\033[1;31mInvalid option. Try again.\\033[0m";;\n'
        script += '  esac\n'
        script += 'done\n'

    # SCENARIO B: It's a standard sequence of commands (List)
    elif isinstance(data, list):
        script += f'echo -e "\\n\\033[1;32mRun these commands in order:\\033[0m"\n'
        for cmd in data:
             escaped_cmd = cmd.replace('"', '\\"')
             script += f'echo "  > {escaped_cmd}"\n'

    return script, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=True)