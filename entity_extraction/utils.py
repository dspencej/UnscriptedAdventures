# entity_extraction/utils.py

def print_formatted_text(text: str, max_width: int = 80):
    """
    Utility function to print formatted text.
    """
    import textwrap
    paragraphs = text.split('\n\n')
    wrapped_paragraphs = [textwrap.fill(paragraph, width=max_width) for paragraph in paragraphs]
    formatted_text = "\n\n".join(wrapped_paragraphs)
    print(formatted_text)
