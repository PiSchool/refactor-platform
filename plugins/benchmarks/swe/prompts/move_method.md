Task: {task_description}

Code to be Refactored:
{code_to_refactor}

Class content:
{class_content}

Refactoring Operation:
{refactoring_operation}

File Path Before Refactoring:
{file_path_before_refactoring}

Project Structure:
{project_structure}

Instructions:
1. Analyze the code, class content and project structure, then move the method to
   an EXISTING java file in this project.
2. The moved method must become a public static method on the target class.
3. The original call site must be updated to call the moved method via that class.

Apply your change by editing the file(s) in the workspace and saving them. The
saved workspace is what gets evaluated: the declared refactoring must be
detectable in the code, and the project must still compile with its tests
passing. Do not leave placeholders, commented-out code, or partial edits.
