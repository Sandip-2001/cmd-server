from flask import Flask, request

app = Flask(__name__)

# Updated database: Now stores both the command and its description
commands = {
    # Git
    "git-undo": {
        "cmd": "git reset --soft HEAD~1",
        "desc": "Undo last commit but keep changes staged"
    },
    "git-discard": {
        "cmd": "git reset --hard HEAD",
        "desc": "Discard all uncommitted local changes"
    },
    "git-amend": {
        "cmd": "git commit --amend --no-edit",
        "desc": "Add staged changes to the previous commit"
    },
    "git-graph": {
        "cmd": "git log --oneline --graph --decorate --all",
        "desc": "Clean visual view of commit history"
    },
    "git-cleanup": {
        "cmd": "git branch --merged | grep -v '\\*' | xargs -n 1 git branch -d",
        "desc": "Delete all merged local branches"
    },
    
    # Media & Downloads
    "yt-mp4": {
        "cmd": "yt-dlp -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' URL",
        "desc": "Download highest quality MP4"
    },
    "yt-audio": {
        "cmd": "yt-dlp -x --audio-format mp3 URL",
        "desc": "Extract audio as MP3"
    },
    "mkv-split": {
        "cmd": "mkvmerge -o part.mkv --split size:3.8G input.mp4",
        "desc": "Split large video files by file size"
    },
    "ffmpeg-trim": {
        "cmd": "ffmpeg -ss 00:01:00 -to 00:02:30 -i input.mp4 -c copy output.mp4",
        "desc": "Cut video without re-encoding (fast)"
    },
    
    # Network & Ports
    "port-find": {
        "cmd": "lsof -i :5000",
        "desc": "Find which process is using a specific port"
    },
    "port-kill": {
        "cmd": "kill -9 $(lsof -t -i :5000)",
        "desc": "Force kill whatever process is running on a port"
    },
    "my-ip": {
        "cmd": "curl ifconfig.me",
        "desc": "Print public IP address in terminal"
    },
    
    # Python & System
    "py-venv": {
        "cmd": "python3 -m venv venv && source venv/bin/activate",
        "desc": "Create and immediately activate virtualenv"
    },
    "docker-prune": {
        "cmd": "docker system prune -a --volumes",
        "desc": "Clean up all unused images, containers, and volumes"
    }
}

@app.route('/cmd')
def get_command():
    query = request.args.get('q', '').lower()
    
    # Filter matching the query against the key, the command, OR the description
    results = {}
    for k, v in commands.items():
        if query in k.lower() or query in v['cmd'].lower() or query in v['desc'].lower():
            results[k] = v
            
    if not query:
        results = commands

    # Format the output beautifully for the terminal
    response_lines = []
    for k, v in results.items():
        # Example format: 
        # [git-undo] Undo last commit but keep changes staged
        #   > git reset --soft HEAD~1
        response_lines.append(f"[{k}] {v['desc']}")
        response_lines.append(f"  > {v['cmd']}")
        response_lines.append("") # Adds a blank line between entries

    response_text = "\n".join(response_lines)
    
    # If no results found, provide a friendly message
    if not response_text.strip():
        response_text = "No commands found matching your search.\n"

    return response_text, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=True)