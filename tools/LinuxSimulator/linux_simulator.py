import datetime

class LinuxTerminal:
    def __init__(self):
        self.files = ["README.md", "app.py", "BHOS.txt"]
        self.current_path = r"/home/user"
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

        # Tarixçəni və son komandanı qeyd et
        self.history.append(raw_input)
        self.change_dict["last_command"] = raw_input

        user_input_split = raw_input.split()
        command = user_input_split[0]
        arguments = user_input_split[1:]

        if command == "history":
            return "\n".join([f"{i+1} {cmd}" for i, cmd in enumerate(self.history)])

        elif command == "ls":
            return " ".join(sorted(self.files))

        elif command == "pwd":
            return self.current_path

        elif command == "touch":
            if not arguments:
                return "Error: couldn't find the file name"
            new_file = arguments[0]
            if new_file in self.files:
                return "File already exists"
            self.files.append(new_file)
            self.change_dict["modified"] = True
            return f"Added {new_file}"

        elif command == "mkdir":
            if not arguments:
                return "Error: folder name not provided."
            folder = arguments[0] + "/"
            if folder in self.files:
                return f"Error: '{arguments[0]}' already exists."
            self.files.append(folder)
            self.change_dict["modified"] = True
            return ""

        elif command == "rm":
            if not arguments:
                return "Error: file name not provided."
            target = arguments[0]
            if target in self.files:
                self.files.remove(target)
                self.change_dict["modified"] = True
                return f"'{target}' deleted."
            if target + "/" in self.files:
                self.files.remove(target + "/")
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