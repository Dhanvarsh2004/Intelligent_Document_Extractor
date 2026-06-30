import pyodbc
import requests
import os
from dotenv import load_dotenv
import pyodbc

load_dotenv()

CONNECTION_STRING = os.getenv("SQL_CONNECTION_STRING")


def insert_success_item(
    document_name,
    month,
    year,
    asset_name,
    mtd_value,
    confidence
):
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO SuccessItems
        (
            DocumentName,
            Month,
            Year,
            AssetName,
            MTDValue,
            Confidence
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            document_name,
            month,
            year,
            asset_name,
            mtd_value,
            confidence
        )
    )

    conn.commit()
    conn.close()
    requests.post(
    "http://127.0.0.1:8000/notify-dashboard"
    )




def insert_review_item(
    document_name,
    month,
    year,
    asset_name,
    mtd_value,
    confidence,
    review_reason
):
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO ReviewItems
        (
            DocumentName,
            Month,
            Year,
            AssetName,
            MTDValue,
            Confidence,
            ReviewReason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            document_name,
            month,
            year,
            asset_name,
            mtd_value,
            confidence,
            review_reason
        )
    )

    conn.commit()
    conn.close()
    requests.post(
    "http://127.0.0.1:8000/notify-dashboard"
    )



def update_dashboard_summary(
    approved_documents=0,
    review_documents=0,
    rejected_documents=0,
    system_status=""
):
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE DashboardSummary
        SET
            ApprovedDocuments = ApprovedDocuments + ?,
            ReviewDocuments = ReviewDocuments + ?,
            RejectedDocuments = RejectedDocuments + ?,
            TotalDocuments = (ApprovedDocuments + ?)
                           + (ReviewDocuments + ?)
                           + (RejectedDocuments + ?),
            SystemStatus = ?,
            LastUpdated = GETDATE()
        WHERE DashboardId = 1
        """,
        (
            approved_documents,
            review_documents,
            rejected_documents,
            approved_documents,
            review_documents,
            rejected_documents,
            system_status
        )
    )

    conn.commit()
    conn.close()
    requests.post(
    "http://127.0.0.1:8000/notify-dashboard"
    )



def update_module_status(
    system_status,
    progress_percentage,
    current_document
):
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE ModuleStatus
        SET
            SystemStatus = ?,
            ProgressPercentage = ?,
            CurrentDocument = ?,
            LastUpdated = GETDATE()
        WHERE Id = 1
        """,
        (
            system_status,
            progress_percentage,
            current_document
        )
    )

    conn.commit()
    conn.close()
    requests.post(
    "http://127.0.0.1:8000/notify-dashboard"
    )

def create_dashboard_summary():
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM Dashboard WHERE Id = 1)
    BEGIN
        INSERT INTO DashboardSummary (
            Id,
            TotalDocuments,
            ApprovedDocuments,
            ReviewDocuments,
            RejectedDocuments,
            SystemStatus
        )
        VALUES (
            1,
            0,
            0,
            0,
            0,
            'Idle'
        )
    END
    """)

    conn.commit()
    conn.close()

def create_module_status():
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM ModuleStatus WHERE Id = 1)
        BEGIN
            INSERT INTO ModuleStatus
            (Id, SystemStatus, ProgressPercentage, CurrentDocument, LastUpdated)
            VALUES
            (1, 'Idle', 0, '', GETDATE())
        END
    """)

    conn.commit()
    conn.close()


def approve_review(
        review_id,
        document_name,
        month,
        year,
        asset_name,
        mtd_value
):

    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    # Fetch confidence score
    cursor.execute("""
        SELECT Confidence
        FROM ReviewItems
        WHERE ReviewId = ?
    """, (review_id,))

    row = cursor.fetchone()

    confidence = row[0] if row else None

    # Insert edited values and original confidence
    cursor.execute("""
        INSERT INTO SuccessItems
        (
            DocumentName,
            Month,
            Year,
            AssetName,
            MTDValue,
            Confidence
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        document_name,
        month,
        year,
        asset_name,
        mtd_value,
        confidence
    ))

    # Remove from ReviewItems
    cursor.execute("""
        DELETE FROM ReviewItems
        WHERE ReviewId = ?
    """, (review_id,))

    conn.commit()
    conn.close()


def get_review_items():
    conn = pyodbc.connect(CONNECTION_STRING)
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
            ReviewReason,
            CreatedDate
        FROM ReviewItems
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
            "mtdValue": float(row.MTDValue),
            "confidence": float(row.Confidence),
            "reviewReason": row.ReviewReason,
            "createdDate": str(row.CreatedDate)
        })

    conn.close()

    return result

def get_success_items():
    conn = pyodbc.connect(CONNECTION_STRING)
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
        FROM SuccessItems
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
            "mtdValue": float(row.MTDValue),
            "confidence": float(row.Confidence),
            "processedDate": str(row.ProcessedDate)
        })

    conn.close()

    return result

def get_dashboard_data():
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM SuccessItems")
    approved_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ReviewItems")
    review_count = cursor.fetchone()[0]


    total_documents = (
        approved_count
        + review_count
    )

    cursor.execute("""
        SELECT TOP 1
            SystemStatus,
            ProgressPercentage,
            CurrentDocument
        FROM ModuleStatus
        ORDER BY Id DESC
    """)

    row = cursor.fetchone()

    conn.close()

    return {
        "totalDocuments": total_documents,
        "approvedDocuments": approved_count,
        "reviewDocuments": review_count,
        "systemStatus": row.SystemStatus,
        "progressPercentage": row.ProgressPercentage,
        "currentDocument": row.CurrentDocument
    }

def ErrorLog(
        ErrorMessage,
        document_name
    ):

    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    # Insert edited values and original confidence
    cursor.execute("""
        INSERT INTO ErrorItems
        (
            ErrorCode,
            ErrorMessage,
            DocumentName
        )
        VALUES (?, ?, ?)
    """,
    (
        0,
        ErrorMessage,
        document_name
    ))

    conn.commit()
    conn.close()
