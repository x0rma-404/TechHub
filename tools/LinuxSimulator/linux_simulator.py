import datetime

class LinuxTerminal:
    def __init__(self):
        # File System: {path: content} where content is None for directories
        self.fs = {
            "/home/user/": None,
            "/home/user/README.md": "# TechHub Linux Simulator\nWelcome to the simulation!",
            "/home/user/app.py": "print('Hello TechHub')",
            "/home/user/BHOS.txt": "Baku Higher Oil School",
            "/home/user/docs/": None,
            "/home/user/docs/notes.txt": "Don't forget to study Linux commands."
        }
        self.current_path = "/home/user"
        self.history = []
        self.change_dict = {
            "last_command": None,
            "session_start": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "modified": False
        }

    def _get_full_path(self, target):
        if target.startswith("/"):
            return target
        if target == "~":
            return "/home/user"
        
        path_prefix = self.current_path if self.current_path.endswith("/") else self.current_path + "/"
        full_path = path_prefix + target
        
        # Handle ".."
        if target == "..":
            if self.current_path == "/":
                return "/"
            parts = self.current_path.strip("/").split("/")
            if len(parts) > 1:
                return "/" + "/".join(parts[:-1])
            return "/"
        
        # Handle "."
        if target == ".":
            return self.current_path
            
        return full_path

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
            path_to_ls = self.current_path
            if arguments:
                path_to_ls = self._get_full_path(arguments[0])
            
            if not path_to_ls.endswith("/"):
                path_to_ls += "/"
                
            results = []
            for path in self.fs:
                if path.startswith(path_to_ls) and path != path_to_ls:
                    relative = path[len(path_to_ls):]
                    if "/" not in relative or (relative.count("/") == 1 and relative.endswith("/")):
                        results.append(relative)
            
            if not results and (path_to_ls not in self.fs and path_to_ls.rstrip("/") not in self.fs):
                return f"ls: cannot access '{arguments[0]}': No such file or directory"
                
            return " ".join(sorted(results))

        elif command == "pwd":
            return self.current_path

        elif command == "cd":
            if not arguments or arguments[0] == "~":
                self.current_path = "/home/user"
                return ""
            
            target = arguments[0]
            new_path = self._get_full_path(target)
            
            folder_path = new_path if new_path.endswith("/") else new_path + "/"
            if folder_path in self.fs:
                self.current_path = folder_path.rstrip("/")
                return ""
            elif new_path == "/":
                self.current_path = "/"
                return ""
            else:
                return f"cd: {target}: No such file or directory"

        elif command == "touch":
            if not arguments:
                return "Error: couldn't find the file name"
            filename = arguments[0]
            full_path = self._get_full_path(filename)
            content = " ".join(arguments[1:]) if len(arguments) > 1 else ""
            
            if full_path in self.fs or (full_path + "/") in self.fs:
                return "File or folder already exists"
            
            self.fs[full_path] = content
            self.change_dict["modified"] = True
            return ""

        elif command == "mkdir":
            if not arguments:
                return "Error: folder name not provided."
            dirname = arguments[0]
            full_path = self._get_full_path(dirname)
            if not full_path.endswith("/"):
                full_path += "/"
            
            if full_path in self.fs:
                return f"Error: '{dirname}' already exists."
            
            self.fs[full_path] = None
            self.change_dict["modified"] = True
            return ""

        elif command == "rm":
            if not arguments:
                return "Error: file name not provided."
            target = arguments[0]
            full_path = self._get_full_path(target)
            
            if full_path in self.fs:
                if self.fs[full_path] is None: # It's a directory
                    # Check if it has children
                    has_children = any(p.startswith(full_path + "/") for p in self.fs if p != full_path)
                    if has_children and "-r" not in arguments:
                        return f"rm: cannot remove '{target}': Is a directory"
                    # Remove dir and children
                    self.fs = {p: v for p, v in self.fs.items() if not p.startswith(full_path)}
                else:
                    del self.fs[full_path]
                self.change_dict["modified"] = True
                return ""
            
            full_path_dir = full_path if full_path.endswith("/") else full_path + "/"
            if full_path_dir in self.fs:
                 # It's a directory (matched by adding /)
                if "-r" not in arguments:
                    return f"rm: cannot remove '{target}': Is a directory"
                self.fs = {p: v for p, v in self.fs.items() if not p.startswith(full_path_dir)}
                self.change_dict["modified"] = True
                return ""
                
            return f"Error: '{target}' not found."

        elif command == "cat":
            if not arguments:
                return "usage: cat <file>"
            target = arguments[0]
            full_path = self._get_full_path(target)
            
            if full_path in self.fs and self.fs[full_path] is not None:
                return self.fs[full_path]
            elif (full_path + "/") in self.fs:
                return f"cat: {target}: Is a directory"
            else:
                return f"cat: {target}: No such file or directory"

        elif command == "whoami":
            return "user"

        elif command == "uname":
            if arguments and arguments[0] == "-a":
                return "Linux techhub 5.15.0-generic #1 SMP x86_64 GNU/Linux"
            return "Linux"

        elif command == "cp":
            if len(arguments) < 2:
                return "usage: cp <source> <destination>"
            src = self._get_full_path(arguments[0])
            dst = self._get_full_path(arguments[1])
            
            if src not in self.fs:
                return f"cp: cannot stat '{arguments[0]}': No such file or directory"
            
            if self.fs[src] is None: # Directory
                if "-r" not in arguments:
                    return f"cp: -r not specified; omitting directory '{arguments[0]}'"
                # Copy directory recursively
                src_dir = src if src.endswith("/") else src + "/"
                dst_dir = dst if dst.endswith("/") else dst + "/"
                for p, v in list(self.fs.items()):
                    if p.startswith(src_dir):
                        new_p = p.replace(src_dir, dst_dir)
                        self.fs[new_p] = v
            else:
                self.fs[dst] = self.fs[src]
            
            self.change_dict["modified"] = True
            return ""

        elif command == "mv":
            if len(arguments) < 2:
                return "usage: mv <source> <destination>"
            src = self._get_full_path(arguments[0])
            dst = self._get_full_path(arguments[1])
            
            if src not in self.fs and (src + "/") not in self.fs:
                return f"mv: cannot stat '{arguments[0]}': No such file or directory"
            
            # Handle directory move
            if (src + "/") in self.fs:
                src = src + "/"
                if not dst.endswith("/"): dst += "/"
                for p in list(self.fs.keys()):
                    if p.startswith(src):
                        new_p = p.replace(src, dst)
                        self.fs[new_p] = self.fs.pop(p)
            else:
                self.fs[dst] = self.fs.pop(src)
                
            self.change_dict["modified"] = True
            return ""

        elif command == "find":
            if not arguments:
                return "."
            path = self._get_full_path(arguments[0])
            name_filter = None
            if "-name" in arguments:
                idx = arguments.index("-name")
                if idx + 1 < len(arguments):
                    name_filter = arguments[idx + 1].strip('"').strip("'")
            
            results = []
            search_prefix = path if path.endswith("/") else path + "/"
            for p in self.fs:
                if p.startswith(search_prefix) or p == path:
                    name = p.rstrip("/").split("/")[-1]
                    if not name_filter or name == name_filter:
                        results.append(p)
            
            return "\n".join(sorted(results))

        elif command == "man":
            if not arguments:
                return "What manual page do you want?"
            cmd = arguments[0]
            manuals = {
                "ls": "ls - list directory contents",
                "cd": "cd - change the shell working directory",
                "pwd": "pwd - print name of current/working directory",
                "cat": "cat - concatenate files and print on the standard output",
                "touch": "touch - change file timestamps / create empty files",
                "mkdir": "mkdir - make directories",
                "rm": "rm - remove files or directories",
                "cp": "cp - copy files and directories",
                "mv": "mv - move (rename) files",
                "whoami": "whoami - print effective userid",
                "uname": "uname - print system information",
                "find": "find - search for files in a directory hierarchy",
                "nano": "nano - Nano's ANOther editor, an enhanced free Pico clone",
                "echo": "echo - display a line of text",
                "history": "history - GNU History Library",
                "clear": "clear - clear the terminal screen",
                "exit": "exit - cause the shell to exit",
                "date": "date - print or set the system date and time"
            }
            return manuals.get(cmd, f"No manual entry for {cmd}")

        elif command == "nano":
            if not arguments:
                return "usage: nano <file> [content]"
            filename = arguments[0]
            full_path = self._get_full_path(filename)
            
            # Interactive mode if only filename provided
            if len(arguments) == 1:
                if full_path in self.fs and self.fs[full_path] is None:
                    return f"nano: {filename}: Is a directory"
                
                content = self.fs.get(full_path, "")
                return {
                    "__nano_edit__": True,
                    "filename": filename,
                    "full_path": full_path,
                    "content": content
                }
            
            # Non-interactive mode if content provided (legacy support)
            content = " ".join(arguments[1:])
            
            if full_path.endswith("/") or (full_path in self.fs and self.fs[full_path] is None):
                return f"nano: {filename}: Is a directory"
            
            self.fs[full_path] = content
            self.change_dict["modified"] = True
            return f"Saved {filename}"

        elif command == "echo":
            return " ".join(arguments)

        elif command == "date":
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        elif command == "clear":
            return ""

        elif command == "exit":
            return "__exit__"

        else:
            available = "ls, pwd, touch, mkdir, rm, echo, date, clear, exit, history, cat, whoami, uname, cp, mv, find, man, nano"
            return f"'{command}' command not found. Available commands: {available}"
