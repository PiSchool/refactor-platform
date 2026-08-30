{{ task.instructions }}

Constraints:

- Perform the {{ params.refactoring }} and nothing else. Unrelated rewrites,
  reformatting or renames elsewhere are failures, not improvements.
- Keep the public behaviour of `{{ params.module }}` identical. The project's
  own test suite is run against your saved workspace: `{{ params.tests }}`.
- Edit the repository in your working directory and save your changes. Do not
  commit, do not leave placeholders, do not create new top-level files.
