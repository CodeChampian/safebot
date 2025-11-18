# SafeBot - AI Supply Chain Risk Analyzer

## What is SafeBot?

SafeBot is an intelligent supplier risk assessment platform designed to help procurement teams evaluate and manage supplier relationships through comprehensive risk analysis and document management. The platform combines AI-powered risk assessment with modern supplier management capabilities to provide procurement teams with the insights they need to make informed decisions.

## 🌟 Key Features

### Supplier Management

- **Complete CRUD Operations**: Create, read, update, and delete supplier profiles
- **Rich Supplier Data**: Store comprehensive supplier information (name, category, location, contact details, description)
- **Real-time Status Management**: Toggle supplier active/inactive status with immediate KPI updates
- **Interactive Dashboard**: Grid view of all suppliers with filtering and search capabilities

### Document Management

- **Multi-format Upload**: Support for PDF, DOCX, PNG, JPG, JPEG files
- **Bulk Upload**: Upload multiple files simultaneously per supplier
- **File Preview**: Live preview of PDF and image files in browser
- **Organized Storage**: Automatic file organization by supplier with metadata tracking

### Risk Assessment

- **AI-Powered Analysis**: Advanced synthetic signal retrieval for accurate risk detection
- **Evidence-Based Results**: Receive risk ratings with specific document references
- **Flexible Querying**: Analyze individual suppliers or comprehensive risk assessment across all data
- **Real-time Processing**: Instant risk evaluations with supporting evidence

### Analytics & Monitoring

- **Live KPIs**: Real-time dashboard showing Total suppliers and Active count
- **Status Tracking**: Instant updates when supplier status changes
- **Document Analytics**: Track document upload counts and file types per supplier

## How It Works

1. **Data Ingestion**: Supplier documents (PDFs, reports, financial statements) are stored in a vector database with metadata
2. **Query Processing**: When you ask a risk-related question, the system generates a "synthetic signal" - a hypothetical analysis paragraph
3. **Smart Retrieval**: This synthetic text is converted to vectors and used to find the most relevant supplier documents
4. **Risk Analysis**: An AI model analyzes the retrieved documents and your question to produce a risk assessment
5. **Evidence Presentation**: Results include risk level, summary, and specific document references

## Project Structure

safebot/
├── server/
│ ├── api/ # FastAPI REST endpoints
│ ├── uploads/ # Document storage directory
│ └── requirements.txt # Python dependencies
├── client/
│ ├── public/ # Static web assets
│ ├── src/
│ │ ├── widgets/ # React UI components
│ │ ├── components/ui/ # Reusable UI components
│ │ ├── api/ # Client-server communication
│ │ └── lib/ # Utility functions
│ └── package.json # Node.js dependencies
├── .env.example # Environment configuration template
├── README.md # Project documentation
└── uploads/ # Global document storage

## Quick Start Guide

### 1. Clone and Setup

```bash
git clone <repository-url>
cd supply-chain-risk
```

### 2. Backend Setup

```bash
cd server
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn api.main:app --reload
```

### 3. Frontend Setup (New Terminal)

```bash
cd client
npm install
npm run dev
```

### 4. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## What You Can Do

### Risk Assessment Queries

- **Financial Risk**: "Does this supplier show signs of financial distress?"
- **Operational Risk**: "Are there any supply chain disruptions mentioned?"
- **Compliance Risk**: "Has this vendor been involved in any regulatory issues?"
- **Geopolitical Risk**: "Is there political instability in the supplier's region?"

### Supplier Analysis

- Analyze specific suppliers by selecting them from the dropdown
- Get comprehensive risk profiles with evidence
- Compare multiple suppliers simultaneously
- Review historical risk trends

### Supplier Management

- Create new supplier profiles with detailed information
- View all suppliers in an interactive dashboard with filtering
- Update supplier information and maintain supplier history
- Delete suppliers when no longer active

### Document Management

- Upload supplier documents (PDFs, reports, financial statements, contracts)
- Organized document storage by supplier with file type validation
- Document count tracking for each supplier
- Retrieve uploaded document metadata and information

## Example Usage

### Scenario 1: New Supplier Evaluation

1. Select supplier "SUP-22" from the supplier list
2. Ask: "What are the main financial risk indicators for this supplier?"
3. Receive: Risk Level (Moderate), Summary, and Document References

### Scenario 2: Comparative Analysis

1. Select multiple suppliers: "SUP-11", "SUP-22", "SUP-29"
2. Ask: "Which supplier has the strongest financial position?"
3. Get comparative analysis with evidence from each supplier's documents

### Scenario 3: Geopolitical Risk Check

1. Leave supplier selection empty (analyzes all)
2. Ask: "Are there any geopolitical risks affecting our suppliers?"
3. Receive comprehensive analysis across all supplier data

## Requirements

Python 3.9 or newer

Node.js 18+

Milvus or Chroma vector database

API key for your preferred model provider (e.g., OpenRouter, TogetherAI, Anthropic)

## Backend Bootstrapping

Enter the backend folder
cd server

Create & activate a virtual environment

python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows

Install required libraries

pip install -r requirements.txt

Duplicate the .env.example file and set:

MODEL_PROVIDER_KEY

VECTOR_DB_URL

SUPPLIER_DOC_COLLECTION

Check that your vector DB is active

Run the server

uvicorn api.main:app --reload

## Frontend Bootstrapping

Move into the UI folder
cd client

Pull dependencies
npm install

Start the local development environment
npm run dev

## Data Preparation

Upload supplier dossiers (annual reports, invoices, sanctions lists, ESG reports) into your vector DB.

Each document must contain metadata with fields like:

{
"vendor_id": "SUP12345",
"category": "financial",
"period": "2023"
}

## Capabilities

### Primary Purpose

The tool identifies levels of supplier risk using documents, numerical data, and geopolitical indicators.

### Functional Highlights

⭐ Supplier Risk Questions

Ask questions such as:

"Does Vendor A show liquidity concerns?"

"Is there any indication of political instability in the vendor's operating region?"

The system responds with a risk rating (Low, Moderate, High) and a justification.

⭐ Intelligent Document Retrieval

Uses a synthetic-signal technique that works like this:

User provides a risk-related question

The model creates a fabricated analytical snippet representing what an answer might look like

That synthetic text is embedded into vectors

The vector DB returns documents whose content aligns with the generated snippet

The final model uses both the user's question and retrieved evidence to generate a risk score

This significantly increases recall accuracy for procurement data.

⭐ Vector Database Integration

Stores and retrieves:

financial statements

news extractions

ESG compliance papers

global watchlist data

⭐ Real-time Scores

The system outputs:

risk level

probability estimate

specific extracted evidence

⭐ Dashboard Features

Supplier selector

Risk-over-time charts

Evidence viewer

File uploader for new vendor documents

### Synthetic-Signal Retrieval (SSR)

Workflow

Accept risk query

Produce a hypothetical analysis paragraph

Encode that paragraph as a vector

Search the vector DB

Compile top findings

Produce a final risk score with supporting references

Benefits

Greatly enhances matching for ambiguous procurement language

Avoids missing key risk signals

Produces more dependable evidence bundles

## REST Endpoints

POST /analyze

Evaluate supplier risk.

Input

{
"query": "Does Vendor X have any credit instability?",
"vendor_ids": ["SUP-22", "SUP-29"]
}

Output

{
"risk_level": "Moderate",
"evidence": [
"SUP-22_annual_2023.pdf",
"SUP-22_quarterly_Q2.json"
],
"summary": "Cash-flow volatility noted in the last two statements."
}

GET /suppliers

Returns all vendors with documents.

Output

{
"suppliers": [
"SUP-11",
"SUP-22",
"SUP-29"
]
}

GET /health

Basic service status check.

### Supplier Management Endpoints

GET /api/suppliers

Retrieve all suppliers with their details.

Output

{
"suppliers": [
{
"id": "SUP-001",
"name": "TechSolutions Inc.",
"category": "Technology",
"location": "USA",
"riskLevel": "Low",
"contact_email": "contact@techsolutions.com",
"contact_phone": "+1-555-0101",
"description": "Leading provider of enterprise software solutions",
"document_count": 3,
"last_assessment": "2025-11-18T19:30:00.000Z",
"created_at": "2025-11-18T19:30:00.000Z"
}
]
}

POST /api/suppliers

Create a new supplier.

Input

{
"name": "New Supplier Corp",
"category": "Manufacturing",
"location": "Germany",
"contact_email": "info@newsupliercorp.com",
"contact_phone": "+49-30-12345678",
"description": "Specialized manufacturing company"
}

Output

{
"supplier": {
"id": "SUP-ABC123",
"name": "New Supplier Corp",
"category": "Manufacturing",
"location": "Germany",
"riskLevel": "Low",
"contact_email": "info@newsupliercorp.com",
"contact_phone": "+49-30-12345678",
"description": "Specialized manufacturing company",
"document_count": 0,
"last_assessment": "2025-11-18T19:30:00.000Z"
}
}

PUT /api/suppliers/{supplier_id}

Update an existing supplier.

DELETE /api/suppliers/{supplier_id}

Delete a supplier.

POST /api/suppliers/{supplier_id}/documents

Upload a document for a supplier. Supports PDF, DOCX, PNG, JPG, JPEG files with bulk upload capability.

Output

{
"message": "Document uploaded successfully",
"file_path": "uploads/SUP-001/document-uuid.pdf"
}

GET /api/suppliers/{supplier_id}/documents

Get all documents for a supplier.

Output

{
"documents": [
{
"filename": "contract-2025.pdf",
"file_path": "uploads/SUP-001/contract-2025.pdf",
"size": 245760,
"uploaded_at": "2025-11-18T19:35:00.000Z",
"extension": ".pdf"
}
]
}

## Troubleshooting

### Common Issues

**Frontend won't start**

- Ensure Node.js 18+ is installed
- Run `npm install` in the client directory
- Check if port 5173 is available

**Backend won't start**

- Ensure Python 3.9+ is installed
- Activate virtual environment: `venv\Scripts\activate` (Windows)
- Install dependencies: `pip install -r requirements.txt`
- Check if port 8000 is available

**API Key Errors**

- Verify your `.env` file has correct API keys
- Check API provider status and credits
- Ensure MODEL_PROVIDER_KEY is set correctly

**Vector Database Connection**

- Ensure Milvus/Chroma is running
- Check VECTOR_DB_URL in `.env`
- Verify SUPPLIER_DOC_COLLECTION exists

**No Suppliers Showing**

- Demo suppliers will appear if database is empty
- Upload supplier documents to populate the database
- Check vector database connection

### Performance Tips

- Use specific supplier selection for faster analysis
- Keep queries focused and specific
- Ensure vector database is properly indexed
- Monitor API usage limits

## Architecture Overview

### Backend (FastAPI)

- **API Layer**: REST endpoints for risk analysis and supplier management
- **Supplier Management**: CRUD operations for supplier profiles and document handling
- **Document Management**: File upload, validation, and organization by supplier
- **Processing Layer**: Risk scoring and analysis logic
- **Data Layer**: Vector database integration and in-memory supplier storage
- **Config Layer**: Environment and settings management

### Frontend (React)

- **Components**: Modular UI building blocks
- **API Integration**: Client-server communication
- **State Management**: Real-time analysis updates
- **Responsive Design**: Mobile-friendly interface

### Data Flow

**Risk Assessment Flow:**

1. User submits query via frontend
2. Frontend sends request to backend API
3. Backend generates synthetic signal
4. Vector search retrieves relevant documents
5. AI model analyzes documents and query
6. Results returned with risk assessment

**Supplier Management Flow:**

1. User creates/updates supplier via frontend form
2. Frontend sends supplier data to backend API
3. Backend validates and stores supplier information
4. Documents can be uploaded and associated with suppliers
5. Frontend updates to show new/updated supplier data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Developer Notes

Backend defaults to http://localhost:8000

Frontend runs at http://localhost:5173

Auto-generated documentation at /docs

Vector dashboard at its respective port (Milvus / Chroma UI)

File serving available at /files endpoint for uploaded documents

Supported file formats: PDF, DOCX, PNG, JPG, JPEG

Multiple file uploads supported per supplier
