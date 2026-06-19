import os
import json
import re
import sys
import time
from pathlib import Path

from extraction.pdf_extractor import extract_pdf
from chunking.header_chunker import structure_chunk
from chunking.structure_chunker import StructureAwareChunker
from retrieval.financial_retriever import FinancialRetriever
from llm.prompt_builder import build_context, build_prompt
from llm.llm_caller import call_llm
from scoring.confidence_scorer import calculate_confidence
from chunking.Page_chunker import page_chunking
from chunking.PDF_Creator import extract_pages_as_pdf

start = time.time()


#PDF_PATH = Path(input("Enter File path: ").strip().strip('"'))
#fund_name = str(input("Enter Assetname: "))


PDF_PATH = Path(sys.argv[1])
fund_name = sys.argv[2]
folder_path = Path("ExtractedPages")
try:
    for item in folder_path.iterdir():
        if item.is_file():
            item.unlink()
except:
    pass
pages=page_chunking(PDF_PATH)
retriever = FinancialRetriever(pages)
results = retriever.retrieve(
    fund_name=fund_name,
    top_k=2
)
print(results)
page_numbers = [item['pageno'] for item in results]
print(page_numbers)

extract_pages_as_pdf(PDF_PATH, page_numbers)
# Extract PDF
text = ""

for file in folder_path.iterdir():
    text += extract_pdf(file) + "\n\n"

# Optional save
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(text)

Header_chunks = structure_chunk(text)

chunker = StructureAwareChunker(
    chunk_size=200,
    chunk_overlap=50
)

chunks = chunker.create_chunks(Header_chunks)


with open("chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=4, ensure_ascii=False)


retriever = FinancialRetriever(chunks)

top_chunks = retriever.retrieve(
    fund_name=fund_name,
    top_k=5
)

for chunk in top_chunks:
    print(chunk)
    print("="*80)

context = build_context(top_chunks)

with open("output - Copy.txt", "w", encoding="utf-8") as f: 
    f.write(context)

# Prompt
prompt = build_prompt(fund_name, context)

result = call_llm(prompt)

print(f"Total Time: {time.time() - start:.2f}s")
print("\nLLM OUTPUT:\n")
print(result)

try:
    try:
        # Try parsing directly
        parsed = json.loads(result)

    except json.JSONDecodeError:
        # If parsing fails, remove markdown code fences and try again
        cleaned_result = (
            result
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        parsed = json.loads(cleaned_result)

    confidence_score = calculate_confidence(
        parsed,
        text
    )

    parsed["confidence_score"] = confidence_score

    with open(
        "extracted_fields.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(parsed, f, indent=4)

    print("\nFinal JSON:\n")
    print(json.dumps(parsed, indent=4))

    print(f"\nConfidence Score: {confidence_score}%")

    print("\nSaved → extracted_fields.json")

except Exception as e:
    print("JSON parse error:", e)
    print("\nRaw output:")
    print(result)
