# Lessons
- Keep all shell-agnostic for Linux/Windows
- Always run UI test and check the logs for errors before finishing a request that modifies the code

- For UI features backed by external state like SQLite, always surface connection/read status in the UI itself so "no data" is distinguishable from "not connected"
- If a Gradio panel depends on runtime polling, also initialize it on page load and input changes so the user sees the state immediately
