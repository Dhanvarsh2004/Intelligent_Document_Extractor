import pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=310823DE549002;"
    "DATABASE=AgenticAIPOC;"
    "UID=sa;"
    "PWD=Database@123;"
)

cursor = conn.cursor()

cursor.execute(
    "SELECT COUNT(*) FROM dbo.SuccessItems"
)

count = cursor.fetchone()[0]

print("Success Count:", count)

conn.close()