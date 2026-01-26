import datetime

class LinuxTerminal:
    def __init__(self):
        self.files = [
            "/home/user/README.md", 
            "/home/user/app.py", 
            "/home/user/BHOS.txt",
            "/home/user/docs/",
            "/home/user/docs/notes.txt"
        ]
        self.current_path = "/home/user"
        self.history = []
        self.change_dict = {
            "last_command": None,
            "session_start": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "modified": False
        }

    def run_command(self, user_input):
        raw_input = user_input.strip()
        if not raw_input:
            return ""

        self.history.append(raw_input)
        self.change_dict["last_command"] = raw_input

        user_input_split = raw_input.split()
        command = user_input_split[0]
        arguments = user_input_split[1:]

        if command == "history":
            return "\n".join([f"{i+1} {cmd}" for i, cmd in enumerate(self.history)])

        elif command == "ls":
            path_prefix = self.current_path if self.current_path.endswith("/") else self.current_path + "/"
            
            results = []
            for f in self.files:
                if f.startswith(path_prefix) and f != path_prefix:
                    relative = f[len(path_prefix):]
                    if "/" not in relative or (relative.count("/") == 1 and relative.endswith("/")):
                        results.append(relative)
            
            return " ".join(sorted(results))

        elif command == "pwd":
            return self.current_path

        elif command == "cd":
            if not arguments or arguments[0] == "/" or arguments[0] == "~":
                self.current_path = "/home/user"
                return ""
            
            target = arguments[0]
            
            if target == "..":
                if self.current_path != "/":
                    parts = self.current_path.strip("/").split("/")
                    if len(parts) > 1:
                        self.current_path = "/" + "/".join(parts[:-1])
                    else:
                        self.current_path = "/"
                return ""
            
            if target == ".":
                return ""

            new_path = self.current_path if self.current_path.endswith("/") else self.current_path + "/"
            new_path += target
            
            folder_path = new_path if new_path.endswith("/") else new_path + "/"
            if folder_path in self.files or folder_path == "/home/user/":
                self.current_path = folder_path.rstrip("/")
                return ""
            else:
                return f"cd: {target}: No such file or directory"

        elif command == "touch":
            if not arguments:
                return "Error: couldn't find the file name"
            filename = arguments[0]
            path_prefix = self.current_path if self.current_path.endswith("/") else self.current_path + "/"
            full_path = path_prefix + filename
            
            if full_path in self.files or (full_path + "/") in self.files:
                return "File or folder already exists"
            
            self.files.append(full_path)
            self.change_dict["modified"] = True
            return f"Added {filename}"

        elif command == "mkdir":
            if not arguments:
                return "Error: folder name not provided."
            dirname = arguments[0]
            path_prefix = self.current_path if self.current_path.endswith("/") else self.current_path + "/"
            full_path = path_prefix + dirname + "/"
            
            if full_path in self.files:
                return f"Error: '{dirname}' already exists."
            
            self.files.append(full_path)
            self.change_dict["modified"] = True
            return ""

        elif command == "rm":
            if not arguments:
                return "Error: file name not provided."
            target = arguments[0]
            path_prefix = self.current_path if self.current_path.endswith("/") else self.current_path + "/"
            
            full_path = path_prefix + target
            if full_path in self.files:
                self.files.remove(full_path)
                self.change_dict["modified"] = True
                return f"'{target}' deleted."
            
            full_path_dir = full_path if full_path.endswith("/") else full_path + "/"
            if full_path_dir in self.files:
                self.files = [f for f in self.files if not f.startswith(full_path_dir)]
                self.change_dict["modified"] = True
                return f"'{target}' deleted."
                
            return f"Error: '{target}' not found."

        elif command == "echo":
            return " ".join(arguments)

        elif command == "date":
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        elif command == "clear":
            return ""

        elif command == "exit":
            return "__exit__"

        else:
            available = "ls, pwd, touch, mkdir, rm, echo, date, clear, exit, history"
            return f"'{command}' command not found. Available commands: {available}"