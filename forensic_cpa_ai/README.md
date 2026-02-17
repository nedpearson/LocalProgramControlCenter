# Forensic CPA AI - Document Processing System

A Flask-based web application for forensic accounting document analysis and processing. This system provides automated extraction and analysis of financial documents including PDFs, Excel spreadsheets, and Word documents.

## Features

- **PDF Processing**: Extract text, tables, and metadata from PDF documents
- **Excel Analysis**: Parse spreadsheets, analyze numeric data, and generate statistics
- **Word Document Processing**: Extract text, tables, and structural information
- **REST API**: Simple HTTP API for document upload and analysis
- **File Management**: Track uploaded files and their processing status

## Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## Installation

### Option 1: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Direct Installation

```bash
pip install -r requirements.txt
```

## Running the Application

### Basic Start

```bash
python main.py
```

The server will start on `http://localhost:5000` by default.

### Custom Port

```bash
# Set PORT environment variable
PORT=5000 python main.py

# Or on Windows:
set PORT=5000 && python main.py
```

### Debug Mode

```bash
# Enable Flask debug mode
FLASK_DEBUG=true python main.py

# Or on Windows:
set FLASK_DEBUG=true && python main.py
```

## API Endpoints

### GET /
Get API information and available endpoints.

**Response:**
```json
{
  "application": "Forensic CPA AI",
  "version": "1.0.0",
  "endpoints": {...},
  "supported_formats": ["PDF", "Excel", "Word"]
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-02-17T12:00:00",
  "service": "Forensic CPA AI"
}
```

### POST /api/upload
Upload and process a document.

**Parameters:**
- `file`: Document file (multipart/form-data)

**Supported formats:**
- PDF (.pdf)
- Excel (.xlsx, .xls)
- Word (.docx, .doc)

**Example:**
```bash
curl -X POST -F "file=@document.pdf" http://localhost:5000/api/upload
```

**Response:**
```json
{
  "success": true,
  "file_id": "20240217_120000_document.pdf",
  "filename": "document.pdf",
  "file_type": "pdf",
  "processed_at": "2024-02-17T12:00:00",
  "results": {...}
}
```

### GET /api/analyze/<file_id>
Get analysis results for a processed file.

**Example:**
```bash
curl http://localhost:5000/api/analyze/20240217_120000_document.pdf
```

### GET /api/files
List all uploaded and processed files.

**Response:**
```json
{
  "count": 5,
  "files": [
    {
      "file_id": "20240217_120000_document.pdf",
      "filename": "document.pdf",
      "size": 12345,
      "uploaded_at": "2024-02-17T12:00:00",
      "has_results": true
    }
  ]
}
```

## Document Processing Features

### PDF Processing
- Extracts text from all pages
- Identifies and extracts tables
- Retrieves document metadata (creator, producer, page count)
- Preserves page structure

### Excel Processing
- Reads all sheets in a workbook
- Generates data previews (first 10 rows)
- Identifies column types (numeric, text, date)
- Calculates statistics for numeric columns
- Provides row and column counts

### Word Processing
- Extracts all paragraphs with styling information
- Extracts all tables with full data
- Provides document structure metadata
- Maintains paragraph numbering

## Project Structure

```
forensic_cpa_ai/
├── main.py              # Flask application
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── .env.example        # Environment variables template
├── uploads/            # Uploaded files (auto-created)
└── local-nexus.bundle.json  # Local Nexus Controller import bundle
```

## Configuration

Create a `.env` file for configuration:

```env
PORT=5000
FLASK_DEBUG=false
MAX_UPLOAD_SIZE=16777216  # 16MB in bytes
```

## Integration with Local Nexus Controller

This application is designed to work with the Local Nexus Controller. To register it:

1. Copy the `local-nexus.bundle.json` file
2. Import it via the Local Nexus Controller dashboard
3. Or use the command line:
   ```bash
   python tools/import_bundle.py /path/to/local-nexus.bundle.json
   ```

## Security Notes

- Maximum file upload size is 16MB by default
- Only specific file types are allowed (PDF, Excel, Word)
- File names are sanitized using `secure_filename`
- Uploaded files are stored locally in the `uploads` folder

## Troubleshooting

### Port Already in Use
```bash
# Change port using environment variable
PORT=5001 python main.py
```

### Missing Dependencies
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### Upload Folder Permissions
The application automatically creates the `uploads` folder. If you encounter permission errors, ensure the application has write access to its directory.

## Future Enhancements

- [ ] AI-powered document analysis
- [ ] Automated anomaly detection
- [ ] Financial ratio calculations
- [ ] PDF report generation
- [ ] Database storage for processed documents
- [ ] User authentication
- [ ] Document comparison features
- [ ] Export analysis results to Excel/PDF

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please contact the development team or create an issue in the project repository.
