NAME = "example_hello"

def register(app_context: dict) -> None:
    app_context.setdefault("plugins_registered", []).append(NAME)
