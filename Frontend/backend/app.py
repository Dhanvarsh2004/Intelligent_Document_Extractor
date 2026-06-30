from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/dashboard')
def dashboard():

    return jsonify({
        "totalDocuments": 25,
        "approvedDocuments": 18,
        "reviewDocuments": 5,
        "rejectedDocuments": 2,
        "systemStatus": "Validation",
        "progressPercentage": 80
    })

if __name__ == '__main__':
    app.run(debug=True)