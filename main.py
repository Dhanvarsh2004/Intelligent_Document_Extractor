import os
import json
import re
import sys
import time
from pathlib import Path
import shutil
from extraction.pdf_extractor import extract_pdf
from chunking.header_chunker import structure_chunk
from chunking.structure_chunker import StructureAwareChunker
from retrieval.financial_retriever import FinancialRetriever
from llm.prompt_builder import build_context, build_prompt
from llm.llm_caller import call_llm
from scoring.confidence_scorer import calculate_final_confidence
from chunking.Page_chunker import page_chunking
from chunking.PDF_Creator import extract_pages_as_pdf
from Encryption.Chunk_Encryption import encrypt_chunks
import FastAPI.StatusDB as DB
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()



def main():
    print("Main started")
    start = time.time()
    # PDF_PATH = Path(input("Enter File path: ").strip().strip('"'))
    # fund_name = str(input("Enter Assetname: "))
    APPROVED_FOLDER = Path("Approved Documents")
    REJECTED_FOLDER = Path("Rejected Documents")

    # Create folders if they don't exist
    APPROVED_FOLDER.mkdir(exist_ok=True)
    REJECTED_FOLDER.mkdir(exist_ok=True)

    PDF_PATH = Path(sys.argv[1])
    fund_name = sys.argv[2]
    folder_path = Path("ExtractedPages")
    file_name=PDF_PATH.name
    print(PDF_PATH)
    BASE_DIR = Path(__file__).resolve().parent
    destination = BASE_DIR /"Documents"/"Error_Folder"

    DB.update_module_status(
        current_document=file_name,
        system_status="Retrieving Pages",
        progress_percentage=20,
    )


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

    extracted_PDF_Path=extract_pages_as_pdf(PDF_PATH, page_numbers)
    #Encrypted_folder_path=page_encryption(extracted_PDF_Path)

    # Extract PDF


    DB.update_module_status(
        current_document=file_name,
        system_status="Extracting PDF",
        progress_percentage=40,
    )

    text = extract_pdf(extracted_PDF_Path) 

    # Optional save
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(text)


    DB.update_module_status(
        current_document=file_name,
        system_status="Chunking",
        progress_percentage=60,
    )

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

    Encryped_Chunks=encrypt_chunks(context)


    DB.update_module_status(
        current_document=file_name,
        system_status="Calling LLM",
        progress_percentage=80,
    )

    # Prompt
    prompt = build_prompt(fund_name, Encryped_Chunks)

    result = call_llm(prompt)

    print(f"Total Time: {time.time() - start:.2f}s")
    print("\nLLM OUTPUT:\n")
    print(result)
    confidence_score = 0
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
        def safe_int(value):
            try:
                return int(str(value).strip())
            except (ValueError, TypeError):
                return 0



        confidence_score = calculate_final_confidence(
            chunks=chunks,
            asset_name=parsed["fund_name"],
            website_asset_names=[fund_name],
            month_num=parsed["Month"],
            year = safe_int(parsed.get("Year")),
            mtd=float(parsed["MTD"].replace("%", "")),
            model_confidence=parsed["LLMConfidence_Score"]
        )

        DB.update_module_status(
        current_document=file_name,
        system_status="Calculating Confidence",
        progress_percentage=90,
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
        destination.mkdir(exist_ok=True)

        shutil.move(
            PDF_PATH,
            destination / Path(PDF_PATH).name
        )
        print("JSON parse error:", e)
        print("\nRaw output:")
        print(result)
        DB.update_module_status(
        current_document="No documents available",
        system_status="Start",
        progress_percentage=0,
    )
        return
    from decimal import Decimal
    def to_decimal(value):
        if value is None:
            return Decimal("0")

        # Convert to string and remove everything except digits, '.' and '-'
        cleaned = re.sub(r"[^0-9.-]", "", str(value))

        # Handle empty strings
        if cleaned in ("", "-", "."):
            return Decimal("0")

        return Decimal(cleaned)

    status = ""
    if confidence_score >= 85:
        status = "Approved"

    elif confidence_score >= 75:
        status = "Review"
    else:
        status="Rejected"
    def safe_int(value):
        try:
            return int(str(value).strip())
        except (ValueError, TypeError):
            return 0
    try:
        if status == "Approved":
            DB.insert_success_item(
                document_name=file_name,
                month=parsed["Month"],
                year = safe_int(parsed.get("Year")),
                asset_name=parsed["fund_name"],
                mtd_value=to_decimal(parsed["MTD"]),
                confidence=to_decimal(confidence_score)

            )

        elif status == "Review":
            DB.insert_review_item(
                document_name=file_name,
                month=parsed["Month"],
                year = safe_int(parsed.get("Year")),
                asset_name=parsed["fund_name"],
                mtd_value=to_decimal(parsed["MTD"]),
                confidence=to_decimal(parsed["confidence_score"]),
                review_reason="Not required"
            )
            DB.update_module_status(
            current_document=file_name,
            system_status="Completed",
            progress_percentage=100,
        )

        BASE_DIR = Path(__file__).resolve().parent
        if status == "Approved":
            destination = BASE_DIR /"Documents"/"approved documents"
        elif status == "Review":
            destination = BASE_DIR /"Documents"/"review documents"
        elif status=="Rejected":
            pass
        
        destination.mkdir(exist_ok=True)

        shutil.move(
            PDF_PATH,
            destination / Path(PDF_PATH).name
        )
        DB.update_module_status(
            current_document="No documents available",
            system_status="Start",
            progress_percentage=0,
        )
    except Exception as e:
        destination.mkdir(exist_ok=True)

        shutil.move(
            PDF_PATH,
            destination / Path(PDF_PATH).name
        )
        print("error",e)
        DB.ErrorLog(
        e,
        file_name
        )
        DB.update_module_status(
            current_document="No documents available",
            system_status="Start",
            progress_percentage=0,
        )
if __name__ == "__main__":
    main()
