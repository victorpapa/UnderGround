import os

if __name__ == "__main__":
    os.chdir("D:\\Program Files (x86)\\Courses II\\Dissertation\\res")
    
    log_file_name = "log_main.txt"
    log_file_path = os.path.join(os.getcwd(), log_file_name)
    log_file_handler = open(log_file_path, "r", encoding="utf-8")

    suspects_file_name = "suspects.txt"
    suspects_file_path = os.path.join(os.getcwd(), suspects_file_name)
    suspects_file_handler = open(suspects_file_path, "w+", encoding="utf-8")

    for line in log_file_handler:
        if "----->" in line:
            line = line.split()
            # omit the timestamp
            suspects_file_handler.write(" ".join(line[1:]) + "\n")

    
