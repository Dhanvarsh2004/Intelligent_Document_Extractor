import re

def encrypt_chunks(chunks):
    """
    Encrypts sensitive information in text chunks.

    Args:
        chunks (list[str]): List of text chunks.

    Returns:
        list[str]: List of encrypted chunks.
    """

    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'

    phone_pattern = (
        r'\b(?:\+?\d{1,3}[-.\s]?)?'
        r'(?:\(?\d{2,4}\)?[-.\s]?)?'
        r'\d{3,4}[-.\s]?\d{4}\b'
    )

    url_pattern = (
        r'https?://[^\s]+|'
        r'www\.[^\s]+'
    )

    encrypted_chunks = []

    for chunk in chunks:
        chunk = re.sub(email_pattern, "<EMAIL>", chunk)
        chunk = re.sub(phone_pattern, "<PHONE>", chunk)
        chunk = re.sub(url_pattern, "<URL>", chunk)

        encrypted_chunks.append(chunk)

    return encrypted_chunks