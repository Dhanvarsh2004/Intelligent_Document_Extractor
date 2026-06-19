import re


def structure_chunk(markdown_text):
    sections = re.split(r'(?=^## )', markdown_text, flags=re.MULTILINE)

    chunks = []

    for i, section in enumerate(sections):
        section = section.strip()

        if section:
            title = section.split('\n')[0].replace('##', '').strip()

            chunks.append({
                "chunk_id": i,
                "section_name": title,
                "text": section
            })

    return chunks
