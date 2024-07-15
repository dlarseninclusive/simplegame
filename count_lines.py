import os

def count_lines_of_code(directory):
    total_lines = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), 'r') as f:
                    total_lines += sum(1 for _ in f)
    return total_lines

directory = os.getcwd()  # Get the current working directory
lines_of_code = count_lines_of_code(directory)
print(f"Total lines of code: {lines_of_code}")
