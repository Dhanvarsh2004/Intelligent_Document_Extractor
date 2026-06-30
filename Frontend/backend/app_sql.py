from flask import Flask, jsonify, request
from flask_cors import CORS
import pyodbc
import threading

from test_module import run_test

app = Flask(__name__)
CORS(app)

def get_connection():


    return pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=230124HP840G619;"
        r"DATABASE=AgenticAIPOC;"
        r"Trusted_Connection=yes;"
    )

def update_dashboard_summary():

    print("Updating Dashboard Summary...")

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM dbo.SuccessItems"
    )
    approved_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM dbo.ReviewItems"
    )
    review_count = cursor.fetchone()[0]

    total_documents = (
        approved_count +
        review_count
    )

    cursor.execute("""
       UPDATE dbo.DashboardSummary
       SET
        TotalDocuments = ?,
        ApprovedDocuments = ?,
        ReviewDocuments = ?,
        LastUpdated = GETDATE()
        WHERE DashboardId = 1
    """,
    (
    total_documents,
    approved_count,
    review_count
    ))

    conn.commit()

    conn.close()

@app.route('/dashboard')
def dashboard():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM dbo.SuccessItems"
    )
    approved_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM dbo.ReviewItems"
    )
    review_count = cursor.fetchone()[0]

    total_documents = approved_count + review_count

    cursor.execute("""
    SELECT TOP 1
        SystemStatus,
        ProgressPercentage,
        CurrentDocument
    FROM dbo.ModuleStatus
    WHERE Id = 1
    """)

    row = cursor.fetchone()

    system_status = row.SystemStatus
    progress_percentage = row.ProgressPercentage
    current_document = row.CurrentDocument

    conn.close()

    return jsonify({
    "totalDocuments": total_documents,
    "approvedDocuments": approved_count,
    "reviewDocuments": review_count,
    "rejectedDocuments": 0,
    "systemStatus": system_status,
    "progressPercentage": progress_percentage,
    "currentDocument": current_document
    })



@app.route('/success-items')
def success_items():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            SuccessId,
            DocumentName,
            Month,
            Year,
            AssetName,
            MTDValue,
            Confidence,
            ProcessedDate
        FROM dbo.SuccessItems
        ORDER BY SuccessId DESC
    """)

    rows = cursor.fetchall()

    result = []

    for row in rows:

        result.append({
            "successId": row.SuccessId,
            "documentName": row.DocumentName,
            "month": row.Month,
            "year": row.Year,
            "assetName": row.AssetName,
            "mtdValue": row.MTDValue,
            "confidence": float(row.Confidence),
            "processedDate": str(row.ProcessedDate)
        })

    conn.close()

    return jsonify(result)

@app.route('/review-items')
def review_items():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ReviewId,
            DocumentName,
            Month,
            Year,
            AssetName,
            MTDValue,
            Confidence,
            CreatedDate
        FROM dbo.ReviewItems
        ORDER BY ReviewId DESC
    """)

    rows = cursor.fetchall()

    result = []

    for row in rows:

        result.append({

            "reviewId": row.ReviewId,
            "documentName": row.DocumentName,
            "month": row.Month,
            "year": row.Year,
            "assetName": row.AssetName,
            "mtdValue": row.MTDValue,
            "confidence": float(row.Confidence),
            "processedDate": str(row.CreatedDate)

        })

    conn.close()

    return jsonify(result)


@app.route('/approve-review', methods=['POST'])
def approve_review():

    data = request.get_json()

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO dbo.SuccessItems
        (
            DocumentName,
            Month,
            Year,
            AssetName,
            MTDValue,
            Confidence,
            ProcessedDate
        )
        SELECT
            ?,
            ?,
            ?,
            ?,
            ?,
            Confidence,
            CreatedDate
        FROM dbo.ReviewItems
        WHERE ReviewId = ?
    """,
    (
        data['documentName'],
        data['month'],
        data['year'],
        data['assetName'],
        data['mtdValue'],
        data['reviewId']
    ))

    cursor.execute("""
        DELETE FROM dbo.ReviewItems
        WHERE ReviewId = ?
    """,
    (
        data['reviewId'],
    ))

    conn.commit()

    conn.close()

    update_dashboard_summary()

    return jsonify({
    "message": "Record Approved Successfully"
    })

@app.route('/start-processing', methods=['POST'])
def start_processing():

    threading.Thread(
        target=run_test
    ).start()

    return jsonify({
        "message": "Processing Started"
    })


if __name__ == '__main__':
    app.run(debug=True)
