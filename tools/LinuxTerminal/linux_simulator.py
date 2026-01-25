import datetime

class LinuxTerminal:
    def __init__(self):
        self.files = ["README.md", "app.py", "BHOS.txt"]
        self.current_path = r"/home/user"

    def run_command(self, user_input):
        user_input = user_input.strip().split()
        if not user_input:
            return ""

        command = user_input[0]
        arguments = user_input[1:]

        if command == "ls":
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
            return f"Added {new_file}"

        elif command == "mkdir":
            if not arguments:
                return "Error: folder name not provided."
            folder = arguments[0] + "/"
            if folder in self.files:
                return f"Error: '{arguments[0]}' already exists."
            self.files.append(folder)
            return ""

        elif command == "rm":
            if not arguments:
                return "Error: file name not provided."
            target = arguments[0]
            if target in self.files:
                self.files.remove(target)
                return f"'{target}' deleted."
            if target + "/" in self.files:
                self.files.remove(target + "/")
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
            return f"'{command}' command not found. Available commands: ls, pwd, touch, mkdir, rm, echo, date, clear, exit"