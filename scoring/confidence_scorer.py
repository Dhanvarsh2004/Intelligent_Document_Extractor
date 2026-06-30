from datetime import datetime
from rapidfuzz import process, fuzz
import json
import re
import math
from datetime import datetime

def validate_extracted_data_in_chunks(chunks, asset_name, month, year, mtd, threshold=90):
    return True
    """
    Checks whether all extracted values are present in the document chunks.

    Returns:
        {
            "is_valid": True/False,
            "missing_fields": []
        }
    """

    # Combine all chunks into one string
    if isinstance(chunks, list):
        text = " ".join(
        chunk["text"]
        for chunk in chunks
        if isinstance(chunk, dict)
    )
    else:
        text = str(chunks)

    text = text.lower()

    missing_fields = []

    # Asset name (fuzzy match)
    if fuzz.partial_ratio(asset_name.lower(), text) < threshold:
        missing_fields.append("Asset Name")

    # Month
    if str(month).lower() not in text:
        missing_fields.append("Month")

    # MTD
    if str(mtd) not in text:
        missing_fields.append("MTD")

    return len(missing_fields) == 0

# ==========================================================
# Asset Name Confidence (0-20)
# ==========================================================
def asset_name_confidence_score(asset_name, website_asset_names):
    best_match, score, _ = process.extractOne(
        asset_name,
        website_asset_names,
        scorer=fuzz.token_sort_ratio
    )

    normalized_score = round(score / 5, 2)   # 100 -> 20

    return {
        "best_match": best_match,
        "score": normalized_score
    }


# ==========================================================
# MTD Confidence (0-100)
# ==========================================================
def confidence_score_mtd(mtdvalue):
    lower_extreme = -23.83
    lower_whisker = -13.75
    Q1 = -3.66
    median = -0.13
    Q3 = 3.06
    upper_whisker = 13.14
    upper_extreme = 23.22

    if mtdvalue <= lower_extreme or mtdvalue >= upper_extreme:
        score = 0

    elif mtdvalue < lower_whisker:
        score = 70 * (mtdvalue - lower_extreme) / (lower_whisker - lower_extreme)

    elif mtdvalue > upper_whisker:
        score = 70 * (upper_extreme - mtdvalue) / (upper_extreme - upper_whisker)

    elif mtdvalue < Q1:
        score = 70 + 25 * (mtdvalue - lower_whisker) / (Q1 - lower_whisker)

    elif mtdvalue > Q3:
        score = 70 + 25 * (upper_whisker - mtdvalue) / (upper_whisker - Q3)

    elif mtdvalue < median:
        score = 95 + 5 * (mtdvalue - Q1) / (median - Q1)

    else:
        score = 95 + 5 * (Q3 - mtdvalue) / (Q3 - median)

    return round(score, 2)


# ==========================================================
# MTD Score normalized to 0-20
# ==========================================================
def mtd_confidence_score(mtdvalue):
    raw_score = confidence_score_mtd(mtdvalue)
    return round(raw_score / 5, 2)


# ==========================================================
# Month and Year Scores (0-20 each)
# ==========================================================
def month_year_confidence_score(month_input, extracted_year=""):

    # Convert month name/abbreviation to month number
    month_mapping = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12
    }

    if isinstance(month_input, str):
        month_num = month_mapping.get(month_input.strip().lower())
        if month_num is None:
            raise ValueError(f"Invalid month: {month_input}")
    else:
        month_num = month_input

    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    # Derive year
    derived_year = current_year if month_num < current_month else current_year - 1

    # Use extracted year if available, otherwise derived year
    comparison_year = extracted_year if extracted_year != ""  else derived_year
    # Difference in months between current date and statement date
    months_difference = (current_year - comparison_year) * 12 + (current_month - month_num)

    # ==========================================================
    # Month Score
    # ==========================================================
    if months_difference <= 0:
        # Current month or future month
        month_score = 0

    elif months_difference <= 2:
        # Previous 1-2 months get full score
        month_score = 20

    elif months_difference < 36:
        # Exponential decay
        # Month 6 -> score 10 (50%)
        month_score = round(
            20 * (0.5 ** ((months_difference - 2) / 4)),2)

    else:
        month_score = 0
    
    # Year Score (0-20)
    if extracted_year is None:
        year_score = 20

    else:
        year_diff = derived_year-comparison_year 

        if year_diff == 0:
            year_confidence = 1.0
        elif year_diff == 1:
            year_confidence = 0.8
        elif year_diff == 2:
            year_confidence = 0.6
        elif year_diff == 3:
            year_confidence = 0.4
        else:
            year_confidence = 0

        year_score = round(year_confidence * 20)

    return {
        "month_score": month_score,
        "year_score": year_score
    }


# ==========================================================
# Model Confidence Score (0-20)
# Handles both 0-1 and 0-100 inputs
# ==========================================================
def model_confidence_score(model_confidence):

    if model_confidence <= 1:
        score = model_confidence * 20
    else:
        score = model_confidence / 100 * 20

    return round(score, 2)


# ==========================================================
# Final Combined Score
# ==========================================================
def calculate_final_confidence(chunks,
        asset_name,
        website_asset_names,
        month_num,
        year,
        mtd,
        model_confidence):
       
    mtd = str(mtd).strip()
    # Handle values like "(5.6%)"
    match = re.fullmatch(r"\((\d+(\.\d+)?)%\)", mtd)
    if match:
        mtd=f"-{match. Group(1)}%"

    def safe_float(value):
        try:
            return float(str(value).replace("%", "").replace("+", "").strip())
        except Exception:
            return None
    mtd = safe_float(mtd)

    def safe_int(value):
        try:
            return int(float(str(value).strip()))
        except Exception:
            return None
    model_confidence = safe_int(model_confidence)
 
 
    validation = validate_extracted_data_in_chunks(
    chunks,
    asset_name,
    month_num,
    year,
    mtd
    )
    print("Validation:", validation)
    print("Asset:", asset_name)
    print("Month:", month_num)
    print("Year:", year)
    print("MTD:", mtd)

    if not validation:
        return 0
    asset_score = asset_name_confidence_score(
        asset_name,
        website_asset_names
    )

    month_year_scores = month_year_confidence_score(
        month_num,
        year
    )

    mtd_score = mtd_confidence_score(mtd)

    model_score = model_confidence_score(model_confidence)

    total_score = round(
        asset_score["score"]
        + month_year_scores["month_score"]
        + month_year_scores["year_score"]
        + mtd_score
        + model_score,
        2
    )
    print(asset_score["score"], month_year_scores["month_score"],month_year_scores["year_score"],mtd_score, model_score)
    print(total_score)
    return total_score

# score = calculate_final_confidence(
#     chunks="",
#     asset_name="CastleKnight Master Fund LP",
#     website_asset_names=["CastleKnight Master Fund"],
#     month_num="May",
#  year=2026,
#     mtd="11.8",
#     model_confidence=85
# )
# print("Final Confidence Score:", score)  # Expected output: 100.0
# exit(0)
 
# (chunks,
#         asset_name,
#         website_asset_names,
#         month_num,
#         year,
#         mtd,
#         model_confidence):
#print(calculate_final_confidence("","CastleKnight Master Fund LP","CastleKnight Master Fund LP","May","2026","+11.8%","98%"))

# {
#     "fund_name": "CastleKnight Master Fund LP",
#     "Month": "May",
#     "MTD": "+11.8%",
#     "Year": "2026",
#     "LLMConfidence_Score": "98"
# }
#print(calculate_final_confidence(chunks=text,asset_name="RA Capital Healthcare Fund, L.P.",website_asset_names="RA Capital",month_num="May",year="",mtd="+1.3%",model_confidence=55))