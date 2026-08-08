from flask import Flask, request

app = Flask(__name__)

# Your command database
commands = {
    "git-undo": "git reset --soft HEAD~1",
    "git-amend": "git commit --amend --no-edit",
    "yt-audio": "yt-dlp -x --audio-format mp3 URL",
    "split-vid": "mkvmerge -o part.mkv --split size:3.8G input.mp4"
}

@app.route('/cmd')
def get_command():
    query = request.args.get('q', '').lower()
    
    # Filter commands matching the query
    results = {k: v for k, v in commands.items() if query in k.lower() or query in v.lower()}
    
    # If no query is provided, show everything
    if not query:
        results = commands

    # Format output as plain text so it looks clean in the terminal
    response_text = "\n".join([f"{k}: {v}" for k, v in results.items()])
    
    return response_text + "\n", 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=True)