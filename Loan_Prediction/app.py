# app.py
from flask import Flask, request, jsonify,render_template
import sqlite3
import json
import os
from werkzeug.utils import secure_filename
import PyPDF2
import openai
import datetime


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
openai.api_key = ''  # Replace with your actual API key

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database setup
def init_db():
    conn = sqlite3.connect('loans.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS loan_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_amount REAL,
        annual_income REAL,
        employment_status TEXT,
        loan_purpose TEXT,
        risk_score INTEGER,
        risk_explanation TEXT,
        document_validity BOOLEAN,
        document_issues TEXT,
        timestamp DATETIME
    )
    ''')
    conn.commit()
    conn.close()

init_db()


@app.route('/assess_risk', methods=['POST'])
def assess_risk():
    data = request.json
    
    # Extract loan application details
    loan_amount = data.get('loan_amount')
    annual_income = data.get('annual_income')
    employment_status = data.get('employment_status')
    loan_purpose = data.get('loan_purpose')
    
    # Call OpenAI API for risk assessment (updated for v1.0.0+)
    prompt = f"""
    Assess the risk of this loan application on a scale of 1-10 (1 being lowest risk, 10 being highest risk).
    Provide a brief explanation for your assessment.
    
    Loan Amount: ${loan_amount}
    Annual Income: ${annual_income}
    Employment Status: {employment_status}
    Loan Purpose: {loan_purpose}
    
    Return your response as a JSON object with the keys 'risk_score' (integer 1-10) and 'explanation' (string).
    Make sure to format it as valid JSON.
    """
    
    try:
        # Updated OpenAI API call
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a loan risk assessment AI that evaluates loan applications. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Get the response content
        response_content = response.choices[0].message.content.strip()
        
        # Try to parse it as JSON, and handle the case where it might not be properly formatted
        try:
            ai_response = json.loads(response_content)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'({.*})', response_content.replace('\n', ' '), re.DOTALL)
            if json_match:
                try:
                    ai_response = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    # If we still can't parse it, create a default response
                    ai_response = {
                        'risk_score': 5,
                        'explanation': 'The system encountered an error analyzing the application. Default moderate risk assigned.'
                    }
            else:
                # Default response if we can't extract JSON
                ai_response = {
                    'risk_score': 5,
                    'explanation': 'The system encountered an error analyzing the application. Default moderate risk assigned.'
                }
        
        risk_score = ai_response.get('risk_score')
        explanation = ai_response.get('explanation')
        
        # Store in database
        conn = sqlite3.connect('loans.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO loan_applications (loan_amount, annual_income, employment_status, loan_purpose, risk_score, risk_explanation, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (loan_amount, annual_income, employment_status, loan_purpose, risk_score, explanation, datetime.datetime.now())
        )
        conn.commit()
        app_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'application_id': app_id,
            'risk_score': risk_score,
            'explanation': explanation
        })
    
    except Exception as e:
        print(f"Error assessing risk: {str(e)}")
        return jsonify({
            'error': 'Error assessing risk',
            'message': str(e)
        }), 500

@app.route('/upload_document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    application_id = request.form.get('application_id')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(file_path)
        
        # Verify document with OpenAI (updated for v1.0.0+)
        prompt = f"""
        Analyze this bank statement and check for:
        1. Does the income match or exceed the stated annual income?
        2. Are there any overdrafts or financial irregularities?
        3. Overall financial health assessment.
        
        Bank statement text:
        {extracted_text[:4000]}  # Limiting text length for API
        
        Return your response as a JSON object with the keys 'is_valid' (boolean), 'issues' (array of strings), and 'explanation' (string).
        Make sure to format it as valid JSON.
        """
        
        try:
            # Updated OpenAI API call
            client = openai.OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a document verification AI that checks bank statements for loan applications. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Get the response content
            response_content = response.choices[0].message.content.strip()
            
            # Try to parse it as JSON, and handle the case where it might not be properly formatted
            try:
                ai_response = json.loads(response_content)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from the response
                # This handles cases where the model returns additional text around the JSON
                import re
                json_match = re.search(r'({.*})', response_content.replace('\n', ' '), re.DOTALL)
                if json_match:
                    try:
                        ai_response = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        # If we still can't parse it, create a default response
                        ai_response = {
                            'is_valid': False,
                            'issues': ['Could not properly parse document verification results'],
                            'explanation': 'The system encountered an error analyzing the document. Please try again.'
                        }
                else:
                    # Default response if we can't extract JSON
                    ai_response = {
                        'is_valid': False,
                        'issues': ['Could not properly parse document verification results'],
                        'explanation': 'The system encountered an error analyzing the document. Please try again.'
                    }
            
            is_valid = ai_response.get('is_valid', False)
            issues = ai_response.get('issues', [])
            explanation = ai_response.get('explanation', 'No explanation provided')
            
            # Update database
            conn = sqlite3.connect('loans.db')
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE loan_applications SET document_validity = ?, document_issues = ? WHERE id = ?',
                (is_valid, json.dumps(issues), application_id)
            )
            conn.commit()
            conn.close()
            
            return jsonify({
                'is_valid': is_valid,
                'issues': issues,
                'explanation': explanation
            })
        
        except Exception as e:
            print(f"Error processing document: {str(e)}")
            return jsonify({
                'is_valid': False,
                'issues': ['Error processing document'],
                'explanation': f'An error occurred during document verification: {str(e)}'
            }), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/get_history', methods=['GET'])
def get_history():
    limit = request.args.get('limit', 10)
    
    conn = sqlite3.connect('loans.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM loan_applications ORDER BY timestamp DESC LIMIT ?',
        (limit,)
    )
    applications = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(applications)

@app.route('/')
def index():
    return render_template('index.html')
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text

if __name__ == '__main__':
    app.run(debug=True)