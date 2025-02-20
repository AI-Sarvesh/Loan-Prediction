# Loan Monitoring System

An AI-powered loan application monitoring system that assesses risk, verifies documents, and provides insightful analytics.

## Features

1. **Loan Application Risk Assessment**
   - Submit loan details (amount, income, employment status, purpose)
   - AI-generated risk score (1-10) with explanation
   - Real-time feedback on application viability

2. **Document Verification**
   - PDF bank statement upload and analysis
   - Automated verification of income claims
   - Detection of financial irregularities
   - Validity status with flagged issues

3. **Application Dashboard**
   - Visual representation of risk scores
   - History of applications with status updates
   - At-a-glance view of portfolio risk profile

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **AI Integration**: OpenAI GPT-3.5/4
- **PDF Processing**: PyPDF2
- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Visualization**: Chart.js

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/loan-monitoring-system.git
   cd loan-monitoring-system
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install flask openai PyPDF2 werkzeug
   ```

4. Set up your OpenAI API key:
   - Open `app.py`
   - Replace `'your-openai-api-key'` with your actual OpenAI API key

5. Initialize the database:
   ```
   python app.py
   ```

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Submit a loan application with the required details

4. Upload supporting documents when prompted

5. View risk assessment and document verification results

## Project Structure

```
loan-monitoring-system/
├── app.py              # Flask application with API endpoints
├── loans.db            # SQLite database
├── index.html          # Frontend interface
├── static/             # Static assets (CSS, JS)
├── uploads/            # Temporary storage for uploaded documents
└── README.md           # Project documentation
```

## API Endpoints

- **POST /assess_risk**: Analyze loan application and return risk score
- **POST /upload_document**: Verify uploaded bank statements
- **GET /get_history**: Retrieve recent application history

## Security Considerations

- Implement proper authentication before deployment
- Add rate limiting to prevent API abuse
- Encrypt sensitive data in the database
- Set up proper CORS policies
- Sanitize and validate all user inputs

## Future Enhancements

- Multi-document upload and comparison
- Machine learning model for custom risk scoring
- User authentication and role-based access
- Email notifications for application status updates
- Integration with external credit scoring APIs
- Enhanced data visualization and reporting

## License

This project is licensed under the MIT License - see the LICENSE file for details.