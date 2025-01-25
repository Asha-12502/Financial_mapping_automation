from flask import Flask, request, send_file
from flask_cors import CORS
import json
import os
from mapping_backend_processing import *

app = Flask(__name__)
CORS(app)  # This enables Cross-Origin Resource Sharing


@app.route('/process', methods=['POST'])
def process_files():
    try:
        # Get files from request
        pdf_file = request.files['pdf_file']
        excel_file = request.files['excel_file']
        pages = json.loads(request.form['pages'])
        
        # Save files temporarily
        pdf_path = 'temp_pdf.pdf'
        excel_path = 'temp_excel.xlsx'
        pdf_file.save(pdf_path)
        excel_file.save(excel_path)
        
        result_file = process_financial_statements(
            pdf_path,
            excel_path,
            pages,
            prompt,
            qwen_api_key,
            SYSTEM_PROMPT
        )

        # Clean up temporary files
        os.remove(pdf_path)
        os.remove(excel_path)
        
        # Return the processed file
        return send_file(
            result_file,
            as_attachment=True,
            download_name='processed_financial_statements.xlsx'
        )
        
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
