from flask import Flask, request

app = Flask(__name__)

# Updated database: Now stores both the command and its description
commands = {
    # Setup
    "git-config-name": {
        "cmd": "git config --global user.name \"[firstname lastname]\"",
        "desc": "set a name that is identifiable for credit when review version history"
    },
    "git-config-email": {
        "cmd": "git config --global user.email \"[valid-email]\"",
        "desc": "set an email address that will be associated with each history marker"
    },
    "git-config-color": {
        "cmd": "git config --global color.ui auto",
        "desc": "set automatic command line coloring for Git for easy reviewing"
    },

    # Setup & Init
    "git-init": {
        "cmd": "git init",
        "desc": "initialize an existing directory as a Git repository"
    },
    "git-clone": {
        "cmd": "git clone [url]",
        "desc": "retrieve an entire repository from a hosted location via URL"
    },

    # Stage & Snapshot
    "git-status": {
        "cmd": "git status",
        "desc": "show modified files in working directory, staged for your next commit"
    },
    "git-add": {
        "cmd": "git add [file]",
        "desc": "add a file as it looks now to your next commit (stage)"
    },
    "git-reset-file": {
        "cmd": "git reset [file]",
        "desc": "unstage a file while retaining the changes in working directory"
    },
    "git-diff": {
        "cmd": "git diff",
        "desc": "diff of what is changed but not staged"
    },
    "git-diff-staged": {
        "cmd": "git diff-staged",
        "desc": "diff of what is staged but not yet committed"
    },
    "git-commit": {
        "cmd": "git commit -m \"[descriptive message]\"",
        "desc": "commit your staged content as a new commit snapshot"
    },

    # Branch & Merge
    "git-branch": {
        "cmd": "git branch",
        "desc": "list your branches. a * will appear next to the currently active branch"
    },
    "git-branch-new": {
        "cmd": "git branch [branch-name]",
        "desc": "create a new branch at the current commit"
    },
    "git-checkout": {
        "cmd": "git checkout",
        "desc": "switch to another branch and check it out into your working directory"
    },
    "git-merge": {
        "cmd": "git merge [branch]",
        "desc": "merge the specified branch's history into the current one"
    },

    # Inspect & Compare
    "git-log": {
        "cmd": "git log",
        "desc": "show the commit history for the currently active branch"
    },
    "git-log-compare": {
        "cmd": "git log branchB..branchA",
        "desc": "show the commits on branchA that are not on branchB"
    },
    "git-log-follow": {
        "cmd": "git log-follow [file]",
        "desc": "show the commits that changed file, even across renames"
    },
    "git-diff-compare": {
        "cmd": "git diff branchB...branchA",
        "desc": "show the diff of what is in branchA that is not in branchB"
    },
    "git-show": {
        "cmd": "git show [SHA]",
        "desc": "show any object in Git in human-readable format"
    },

    # Tracking Path Changes
    "git-rm": {
        "cmd": "git rm [file]",
        "desc": "delete the file from project and stage the removal for commit"
    },
    "git-mv": {
        "cmd": "git mv [existing-path] [new-path]",
        "desc": "change an existing file path and stage the move"
    },
    "git-log-stat": {
        "cmd": "git log--stat -M",
        "desc": "show all commit logs with indication of any paths that moved"
    },

    # Ignoring Patterns
    "git-config-excludes": {
        "cmd": "git config --global core.excludesfile [file]",
        "desc": "system wide ignore pattern for all local repositories"
    },

    # Share & Update
    "git-remote-add": {
        "cmd": "git remote add [alias] [url]",
        "desc": "add a git URL as an alias"
    },
    "git-fetch": {
        "cmd": "git fetch [alias]",
        "desc": "fetch down all the branches from that Git remote"
    },
    "git-merge-remote": {
        "cmd": "git merge [alias]/[branch]",
        "desc": "merge a remote branch into your current branch to bring it up to date"
    },
    "git-push": {
        "cmd": "git push [alias] [branch]",
        "desc": "Transmit local branch commits to the remote repository branch"
    },
    "git-pull": {
        "cmd": "git pull",
        "desc": "fetch and merge any commits from the tracking remote branch"
    },

    # Rewrite History
    "git-rebase": {
        "cmd": "git rebase [branch]",
        "desc": "apply any commits of current branch ahead of specified one"
    },
    "git-reset-hard": {
        "cmd": "git reset --hard [commit]",
        "desc": "clear staging area, rewrite working tree from specified commit"
    },

    # Temporary Commits
    "git-stash": {
        "cmd": "git stash",
        "desc": "Save modified and staged changes"
    },
    "git-stash-list": {
        "cmd": "git stash list",
        "desc": "list stack-order of stashed file changes"
    },
    "git-stash-pop": {
        "cmd": "git stash pop",
        "desc": "write working from top of stash stack"
    },
    "git-stash-drop": {
        "cmd": "git stash drop",
        "desc": "discard the changes from top of stash stack"
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