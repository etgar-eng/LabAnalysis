# Lab PDF Analysis Tool

A comprehensive automated system for extracting, analyzing, and visualizing laboratory test results from PDF reports. The tool uses machine learning for lab identification and provides an interactive web interface built with Streamlit.

## Features

- **Automated Lab Detection**: Uses CNN/MobileNetV2 model to identify lab logos from PDFs
- **Multi-Lab Support**: Handles PDFs containing reports from multiple laboratories
- **Data Extraction**: Extracts tables and test results from structured PDF reports
- **Interactive Dashboard**: Streamlit-based web interface with visualization
- **Result Analysis**: 
  - Summary statistics
  - Detection status charts
  - Value distribution histograms
  - Key findings identification
- **Excel Export**: Both raw and formatted results available for download

## Supported Labs

| Lab | Multi-Labs | Single Lab | Multiple Checks |
|-----|------------|------------|-----------------|
| ALS | ✓ | ✗ | ✗ |
| Aminolab | ✓ | ✓ | ✓ |
| Bactochem | ✓ | ✓ | ✓ |
| Element | ✓ | ✗ | ✗ |

**Legend:**
- **Multi-Labs**: Can process PDFs containing multiple lab reports
- **Single Lab**: Can process PDFs with only this lab's report
- **Multiple Checks**: Supports processing multiple test batches/checks in one PDF

## Project Structure

```
lab-pdf-analyzer/
├── app.py                      # Streamlit web application
├── main.py                     # Main processing pipeline
├── functions.py                # Data extraction and processing functions
├── identifier.py               # ML model for logo classification
├── image_extractor.py          # PDF image extraction utilities
├── logging_config.py           # Logging configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker container configuration
├── format.csv                  # Output format template
├── lab_logo_classifier.h5      # Trained ML model
├── ALS/
│   └── params.json            # ALS-specific parameters
├── Bactochem/
│   └── params.json            # Bactochem-specific parameters
├── Aminolab/
│   └── params.json            # Aminolab-specific parameters
└── Element/
    └── params.json            # Element-specific parameters
```

## Installation

### Option 1: Docker (Recommended)

1. **Install Docker Desktop**
   - Download from https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

2. **Build the Docker image**
   ```bash
   docker build -t lab-analyzer .
   ```

3. **Run the container**
   ```bash
   docker run -p 8501:8501 lab-analyzer
   ```

4. **Access the application**
   - Open browser to http://localhost:8501

### Option 2: Local Installation

1. **Install system dependencies**
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install ghostscript libgl1 libglib2.0-0
   ```
   
   **macOS:**
   ```bash
   brew install ghostscript
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Usage

### Web Interface

1. **Select Lab**: Choose the laboratory from the dropdown
2. **Multi-lab Toggle**: Enable if PDF contains multiple lab reports
3. **Upload PDF**: Select your lab report PDF file
4. **Run Analysis**: Click to process the document
5. **View Results**: Navigate through tabs to see:
   - Formatted results with visualizations
   - Raw extracted data
   - Download options

### Command Line

```bash
python main.py --lab ALS --input report.pdf --output results
```

**Arguments:**
- `--lab`: Lab name (ALS, Bactochem, Aminolab, Element)
- `--input`: Path to PDF file
- `--multi`: Enable multi-lab processing (true/false)
- `--output`: Output filename (optional)

## Configuration

### Lab Parameters

Each lab has a `params.json` file containing:
- Test parameter mappings
- Unit conversions
- Synonyms for test names

Example structure:
```json
{
  "pH": {
    "values": ["", "pH"],
    "unit": ""
  },
  "Turbidity": {
    "values": ["NTU", "Turbidity"],
    "unit": "NTU"
  }
}
```

### Format Template

The `format.csv` file defines the output structure with columns:
- `test`: Standard test name
- `units`: Expected units
- `values`: Extracted values (populated during processing)

## Model Training

To retrain the logo classification model:

```bash
python identifier.py
```

Requirements:
- Training images organized in `Logo/` directory
- Subdirectories named after each lab containing logo images
- Minimum 20-30 images per lab recommended

## Output Files

- `df_summary.xlsx`: Raw extracted data with all detected values
- `{lab_name}.xlsx`: Formatted results matched to standard template
- Uploaded PDFs saved to respective lab directories

## Docker Management

**Run in background:**
```bash
docker run -d -p 8501:8501 --name lab-app lab-analyzer
```

**View logs:**
```bash
docker logs -f lab-app
```

**Stop container:**
```bash
docker stop lab-app
docker rm lab-app
```

**Rebuild after changes:**
```bash
docker build -t lab-analyzer . --no-cache
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8501
netstat -ano | findstr :8501

# Use different port
docker run -p 8502:8501 lab-analyzer
```

### PDF Not Processing
- Ensure PDF is not password-protected
- Check if lab is supported
- Verify params.json exists for selected lab

### Model File Missing
- Download or train `lab_logo_classifier.h5`
- Place in project root directory

### Excel Files Not Displaying
- Check file permissions
- Ensure openpyxl is installed
- Verify Excel files are created in working directory

## Dependencies

**Core:**
- Python 3.10+
- TensorFlow 2.13+
- Streamlit 1.28+
- Pandas 1.5+

**PDF Processing:**
- camelot-py
- pdfplumber
- PyMuPDF

**Visualization:**
- Plotly 5.17+
- Matplotlib

See `requirements.txt` for complete list.

## License

[Your License Here]

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/NewFeature`)
3. Commit changes (`git commit -m 'Add NewFeature'`)
4. Push to branch (`git push origin feature/NewFeature`)
5. Open Pull Request

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review log files in `lab_analysis.log`

## Acknowledgments

- TensorFlow team for MobileNetV2
- Camelot developers for PDF table extraction
- Streamlit team for the web framework