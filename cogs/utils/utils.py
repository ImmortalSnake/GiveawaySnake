def codeblock(code: str, language: str) -> str:
    """Adds a codeblock formatting for the code"""
    return f"```{language}\n{code}\n```"