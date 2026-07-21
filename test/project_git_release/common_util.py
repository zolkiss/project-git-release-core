import re


def clean_text(text: str) -> str:
    """
    Needs due to the GH Action runner. It doesn't like the ASCII Color Characters
    :param text: The input text
    :return: The input text stripped from coloring
    """
    ret_text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    ret_text = re.sub(r'\s+', ' ', ret_text)
    return ret_text
