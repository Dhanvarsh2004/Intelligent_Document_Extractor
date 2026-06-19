from langchain_text_splitters import RecursiveCharacterTextSplitter


class StructureAwareChunker:
    def __init__(self, chunk_size=300, chunk_overlap=50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def create_chunks(self, documents):
        chunks = []

        for doc in documents:

            if isinstance(doc, dict):
                text = doc["text"]
            else:
                text = doc

            # Detect markdown table
            if "|" in text and "---" in text:
                chunks.append({
                    "type": "table",
                    "text": text
                })

            else:
                text_chunks = self.splitter.split_text(text)

                for chunk in text_chunks:
                    chunks.append({
                        "type": "text",
                        "text": chunk
                    })

        return chunks
