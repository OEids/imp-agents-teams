# IMP Planner Agent Teams - Setup Instructions

## Prerequisites

- Python 3.10 or higher
- Windows 10/11

## Installation

1. **Extract the folder** to your preferred location (e.g., `C:\claude\agent-teams`)

2. **Install Python dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Configure paths** (optional - can also be done in the app)

   Edit `config/user_config.json`:
   ```json
   {
       "data_directory": "C:\\path\\to\\your\\customer data",
       "templates_directory": "C:\\path\\to\\your\\templates",
       "reports_directory": "reports"
   }
   ```

## Running the Application

**Option 1: Command line**
```
python -m streamlit run app.py
```

**Option 2: Use the batch file**
```
launch_app.bat
```

The terminal will display a local URL (e.g., `http://localhost:8501`). Copy this URL into your browser. The port number may vary each time.

## First-Time Setup

1. Open the app
2. In the sidebar, scroll to **Settings**
3. Set your **Data Directory** (where customer Excel files are stored)
4. Set your **Templates Directory** (where the AA_New template workbooks are)
5. Click Save for each

## Folder Structure

```
agent-teams/
├── app.py              # Main web application
├── config/             # Configuration files
│   ├── settings.py
│   └── user_config.json
├── teams/              # Agent specialists
│   ├── s1_specialist.py    # Structure (finance codes, schools)
│   ├── s2_specialist.py    # Staff (contracts, allowances)
│   └── s3_specialist.py    # Financial (budgets, funding)
├── knowledge/          # Domain knowledge files
├── reports/            # Output files (generated)
└── requirements.txt
```

## Customer Data Structure

Place customer data in subfolders by strand:
```
customer data/
├── S1/          # Structure data files
├── S2/          # Staff data files
└── S3/          # Financial data files
```

## Usage

1. Select a team (S1, S2, or S3) from the sidebar
2. Upload customer Excel files in the **Upload** tab
3. Go to **Process** tab and click **Run Processing**
4. View results in **Results** tab
5. Download the completed template from **Download** tab

## Troubleshooting

**"streamlit is not recognized"**
- Use `python -m streamlit run app.py` instead

**Template not found errors**
- Check that Templates Directory in Settings points to valid templates

**No files processed**
- Ensure customer files are in the correct strand subfolder (S1, S2, or S3)

## Contact

For issues or questions, contact the development team.
