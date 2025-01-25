from flask import Flask, request, send_file
from flask_cors import CORS
import json
import os
import logging
import traceback
from werkzeug.utils import secure_filename
from mapping_backend_processing import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configure maximum file size (e.g., 16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def cleanup_files(*files):
    """Safely cleanup temporary files"""
    for file_path in files:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")

@app.route('/process', methods=['POST'])
def process_files():
    pdf_path = None
    excel_path = None
    print(request.form)
    
    print(request.files)
    try:
        # Validate request files
        if 'pdf_file' not in request.files:
            return 'PDF file is missing', 400
        if 'excel_file' not in request.files:
            return 'Excel file is missing', 400
        if 'pages' not in request.form:
            return 'Pages information is missing', 400

        pdf_file = request.files['pdf_file']
        excel_file = request.files['excel_file']

        # Validate file names
        if pdf_file.filename == '':
            return 'No PDF file selected', 400
        if excel_file.filename == '':
            return 'No Excel file selected', 400

        # Validate file types
        if not pdf_file.filename.lower().endswith('.pdf'):
            return 'Invalid PDF file format', 400
        if not excel_file.filename.lower().endswith(('.xlsx', '.xls')):
            return 'Invalid Excel file format', 400

        # Parse and validate pages
        try:
            pages = json.loads(request.form['pages'])
            if not isinstance(pages, dict):
                return 'Invalid pages format', 400
            
            required_statements = ['income', 'balance', 'cashFlow']
            for statement in required_statements:
                if statement not in pages:
                    return f'Missing page numbers for {statement}', 400
                if not pages[statement]:
                    return f'No pages specified for {statement}', 400
                
                # Validate page numbers
                for page in pages[statement]:
                    if not str(page).isdigit() or int(page) < 1:
                        return f'Invalid page number in {statement}', 400
        except json.JSONDecodeError:
            return 'Invalid JSON format for pages', 400

        # Save files with secure filenames
        pdf_path = secure_filename(pdf_file.filename)
        excel_path = secure_filename(excel_file.filename)

        logger.info(f"Saving PDF to: {pdf_path}")
        logger.info(f"Saving Excel to: {excel_path}")

        try:
            pdf_file.save(pdf_path)
            excel_file.save(excel_path)
        except Exception as e:
            logger.error(f"Error saving files: {str(e)}")
            return 'Failed to save uploaded files', 500

        # Verify files were saved
        if not os.path.exists(pdf_path):
            return 'Failed to save PDF file', 500
        if not os.path.exists(excel_path):
            return 'Failed to save Excel file', 500

        # Process the files
        try:
            result_file = process_financial_statements(
                pdf_path,
                excel_path,
                pages,
                prompt,
                qwen_api_key,
                SYSTEM_PROMPT
            )
        except Exception as e:
            logger.error(f"Error in process_financial_statements: {str(e)}")
            logger.error(traceback.format_exc())
            return 'Error processing financial statements', 500

        # Return the processed file
        try:
            return send_file(
                result_file,
                as_attachment=True,
                download_name='processed_financial_statements.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        except Exception as e:
            logger.error(f"Error sending file: {str(e)}")
            return 'Error sending processed file', 500

    except Exception as e:
        logger.error("Unexpected error:")
        logger.error(traceback.format_exc())
        return f"An unexpected error occurred: {str(e)}", 500

    finally:
        # Clean up temporary files
        cleanup_files(pdf_path, excel_path)

# Error handlers for common HTTP errors
@app.errorhandler(400)
def bad_request(error):
    return {'error': 'Bad Request', 'message': str(error)}, 400

@app.errorhandler(404)
def not_found(error):
    return {'error': 'Not Found', 'message': str(error)}, 404

@app.errorhandler(405)
def method_not_allowed(error):
    return {'error': 'Method Not Allowed', 'message': str(error)}, 405

@app.errorhandler(413)
def request_entity_too_large(error):
    return {'error': 'File Too Large', 'message': 'The uploaded file exceeds the maximum allowed size'}, 413

@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"Internal Server Error: {str(error)}")
    return {'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}, 500

if __name__ == '__main__':
    # Ensure the server runs on port 5000
    app.run(port=5000, debug=True)