import time
from ollama import chat


def call_llm(prompt):
    llm_start = time.time()

    # LLM Call

    response = chat(
        model="gpt-oss:120b-cloud",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0,
        }
    )
    result = response.message.content

    print(f"LLM Time: {time.time() - llm_start:.2f}s")

    return result
