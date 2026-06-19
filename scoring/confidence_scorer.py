import re
from datetime import datetime


current_date = datetime.now()

current_month = current_date.strftime("%B")   # Full month name (e.g., June)
current_year = current_date.year  


# Confidence Score Calculator

def calculate_confidence(extracted, document_text):

    score = 0

    fund_name = str(extracted.get("fund_name", "")).strip()
    month = str(extracted.get("Month", "")).strip()
    mtd = str(extracted.get("MTD", "")).strip()
    year = str(extracted.get("Year", "")).strip()
    LLMConfidence_Score = str(extracted.get("LLMConfidence_Score", "")).strip()
    LLMConfidence_Score=int(LLMConfidence_Score)
    # ---------------------------------------------------
    # Extraction Failure 
    # ---------------------------------------------------
    invalid_values = {"", "null", "n/a", "unknown", "none"}

    if month.lower() in invalid_values or mtd.lower() in invalid_values:
        return 0

    score += (LLMConfidence_Score/ 100) * 20
    # ---------------------------------------------------
    # 1. Completeness (25 points)
    # ---------------------------------------------------
    #fields = [fund_name, month, mtd, year]

    #completeness = sum(
    #    1 for field in fields
    #    if field and field.lower() not in ["null", "n/a", "unknown"]
    #)

    #score += (completeness / 4) * 25
    # ---------------------------------------------------
    # 1. Completeness (25 points)
    # ---------------------------------------------------
    
    if current_date.month == 1:
        previous_month = "december"
        previous_year = str(current_date.year - 1)
    else:
        previous_month = datetime(current_date.year, current_date.month - 1, 1).strftime("%B").lower()
        previous_year = str(current_date.year)

    # Check if the input is either the current month/year or the previous month/year
    if (month.lower() == current_month and year == current_year) or \
    (month.lower() == previous_month and year == previous_year):
        score += 25

    # ---------------------------------------------------
    # 2. Existence in document (25 points)
    # ---------------------------------------------------
  
    existence_matches = 0
    for value in [fund_name, month, year]:

        if value and value.lower() in document_text.lower():
            existence_matches += 1

    if mtd:
        normalized_text = re.sub(r"[,%\s]", "", document_text)
        normalized_mtd = re.sub(r"[,%\s]", "", mtd)

        if normalized_mtd in normalized_text:
            existence_matches += 1

    score += (existence_matches / 4) * 25

    # ---------------------------------------------------
    # 3. Uniqueness (15 points)
    # ---------------------------------------------------
    uniqueness_score = 0

    for value in [month, year, mtd]:

        if not value:
            continue

        occurrences = document_text.lower().count(value.lower())

        if occurrences == 1:
            uniqueness_score += 5

        elif occurrences <= 3:
            uniqueness_score += 3

        else:
            uniqueness_score += 1

    score += min(uniqueness_score, 5)

    # ---------------------------------------------------
    # 4. Position proximity (15 points)
    # ---------------------------------------------------
    try:

        positions = []

        for value in [month, year, mtd]:

            if value:
                pos = document_text.lower().find(value.lower())

                if pos != -1:
                    positions.append(pos)

        if len(positions) >= 2:

            spread = max(positions) - min(positions)

            if spread < 200:
                score += 5

            elif spread < 500:
                score += 3

            elif spread < 1000:
                score += 1

    except:
        pass

    # ---------------------------------------------------
    # 5. Format validation (10 points)
    # ---------------------------------------------------
    format_score = 0

    if re.fullmatch(r"20\d{2}", year):
        format_score += 3

    valid_months = [
        "jan","feb","mar","apr",
        "may","jun","jul","aug",
        "sep","oct","nov","dec"
    ]

    if month.lower()[:3] in valid_months:
        format_score += 3

    if re.search(r"-?\d+(\.\d+)?%?", mtd):
        format_score += 4

    score += format_score

    # ---------------------------------------------------
    # 6. Table quality (10 points)
    # ---------------------------------------------------
    pipe_count = document_text.count("|")

    if pipe_count > 100:
        score += 10

    elif pipe_count > 50:
        score += 7

    elif pipe_count > 20:
        score += 4

    else:
        score += 1

    # ---------------------------------------------------
    # Final score
    # ---------------------------------------------------
    score = round(min(score, 100), 2)

    return score
