def build_context(top_chunks):
    context = ""

    for i, chunk in enumerate(top_chunks, 1):
        context += f"\n### Chunk {i}\n"
        context += chunk["text"]
        context += "\n"

    return context


def build_prompt(fund_name, context):
    prompt = """
You are an Intelligent Document Processing engine.

Target Fund Name:
{fund_name}

Extract ONLY these fields and return ONLY valid JSON.
{{
"fund_name": "",
"Month": "",
"MTD": "",
"Year": "",
"LLMConfidence_Score":""
}}

Fund Matching Rules:

1. First identify the fund in the document that most likely corresponds to the Target Fund Name.
2. Do NOT require an exact string match.
3. Consider abbreviations, acronyms, shortened names, alternate fund naming conventions, and common business name variations.
4. A document fund name may be a shortened version of the Target Fund Name.
5. Examples of valid matching patterns:

   * Full name ↔ abbreviated name
   * Full company name ↔ acronym
   * Fund name with or without legal suffixes
   * Fund name with or without words such as Partners, Capital, Management, Advisors, Fund, LP, LLC, Ltd, Holdings, Investments
6. Match based on overall semantic similarity rather than exact text similarity.
7. If multiple funds are similar, choose the closest match.
8. If no reasonable match exists, return null values.
9. Store the matched document fund name in "fund_name".
10. Pick net returns insted of gross returns

Extraction Rules:

10. Preserve markdown table relationships.
11. Locate the row corresponding to the matched fund.
12.Determine which dimension represents years and which dimension represents months. Do not assume a fixed orientation.
13. Identify dimension that contain year labels (2024, 2025, etc.).
14. Identify all year labels and select the largest year numerically.
15. Once the year is selected, lock onto that year and ignore all other years.
16. For each month in the order:
Dec → Nov → Oct → Sep → Aug → Jul → Jun → May → Apr → Mar → Feb → Jan
look only at the cell corresponding to that month and the selected year.
17. Return the first cell containing a numeric value.
18. Never use a value from another year.
18. Ignore blank, null, dash (-), N/A, or missing month values.
19. Month = identified month.
20. MTD = value under that month.
21. Year = selected year row.
22. Never use values from another fund.
23. Never infer numerical values.
24. Return ONLY valid JSON.
25. If no valid performance table exists:

    a. Search narrative text, emails, notes, comments,
       summaries and paragraphs.

    b. Look for statements describing:
       - month-end return
       - estimated return
       - net return
       - monthly return
       - performance return
       - MTD return

    c. If a return value is associated with a month and year,
       extract it.

    d. Month = month referenced in the text.

    e. Year = year referenced in the text.

    f. MTD = return percentage mentioned.

26. Prefer explicitly stated return values over inferred values.

27. If multiple share classes exist
    (USD Class, Yen Class, etc.),
    return the first performance value associated with the USD class.
28. If there is a performance table take month only from there
29. Assess how confident you are that the extracted Month, MTD, and Year are correct and belong to the matched fund.

30. Return an additional field called "LLMConfidence_Score".

31. The score must be between 0 and 100.

32. Assign confidence based on the quality and consistency of the evidence found in the document.

33. Use the following guidelines:

    - 95-100:
      Values are explicitly present in a well-structured performance table and the Month, MTD, and Year clearly correspond to the same cell intersection.

    - 80-94:
      Values are present in the document with strong evidence, but table orientation or formatting introduces minor ambiguity.

    - 60-79:
      Multiple candidate values exist and some interpretation is required.

    - 40-59:
      Values are inferred from narrative text or partially ambiguous tables.

    - 0-39:
      Weak evidence or high uncertainty.

34. Lower the confidence if multiple possible months, years, or return values are present.

35. Lower the confidence if table structure is corrupted, merged, or difficult to interpret.

36. Lower the confidence if Month, MTD, and Year are obtained from narrative text instead of a performance table.

37. Return only a numeric value for "llm_confidence_score". Do not include explanations.

38. Return only valid JSON.
Document:

{context}
""".format(
    fund_name=fund_name,
    context=context
)

    return prompt
