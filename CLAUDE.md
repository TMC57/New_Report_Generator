# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Report Generator system that creates comprehensive PDF reports for facilities and groups based on data from the CM2W API. It generates two types of reports:

1. **Individual Facility Reports** (`pdfGen.py`) - Detailed reports for specific facilities with consumption data, charts, and analytics
2. **Group Reports** (`GrouPdfGen.py`) - Consolidated reports across multiple facilities/owners

## Development Commands

**Start Development Server:**
```bash
python main.py
```
This automatically opens browser tabs for the main interface and group interface.

**Manual Server Start:**
```bash
uvicorn ApiRest:app --host 0.0.0.0 --port 8000 --reload
```

**Docker Development:**
```bash
docker-compose up
```

## Architecture Overview

**Core Flow:**
1. **Data Fetching** (`model.py`) - Retrieves data from CM2W API using Bearer token authentication
2. **Data Transformation** (`DataTransform.py`) - Enriches and aggregates facility data
3. **Report Generation** (`pdfGen.py`, `GrouPdfGen.py`) - Creates PDFs with ReportLab
4. **Configuration Management** - Web interfaces for facility metadata (`static/table.html`, `static/group_table.html`)

**Key Components:**
- `ApiRest.py` - FastAPI application with endpoints for report generation and configuration
- `model.py` - CM2W API client functions with hardcoded authentication
- Chart modules: `BarCharts.py`, `PieCharts.py`, `scatter.py` for visualizations
- `tables.py` - Table generation for PDF reports
- `Config/` - JSON configuration files for facilities and groups

**API Endpoints:**
- `/Reports_generation` - Generate individual facility reports
- `/Group_Reports_generation` - Generate group reports
- `/` - Facility configuration interface
- `/group-app` - Group configuration interface

## Key Technical Details

**PDF Generation:**
- Uses ReportLab for PDF creation with custom page templates
- Charts generated with matplotlib and embedded as images
- Consistent branding with logos from `images/` directory

**Data Processing:**
- CM2W API provides quantity reports, device lists, stock levels
- Data transformation aggregates by facility/owner with custom logic
- Color mapping system (`colors_map.py`) ensures consistent chart appearance

**Configuration System:**
- Facility metadata stored in `Config/configJson.json` (85KB)
- Group configurations in `Config/GroupConfigJson.json` (28KB)
- Web interfaces allow editing configurations via HTML forms

**File Organization:**
- Generated PDFs output to `Reports/` directory
- Uploaded images stored in `uploads/` directory
- Chart modules follow `{Type}Charts.py` naming pattern

## Important Notes

- **Language**: Comments and UI text are primarily in French
- **Authentication**: Bearer token for CM2W API is hardcoded in `model.py`
- **Port**: Application runs on port 8000
- **Docker**: Includes volume mounts for `Reports/` and `uploads/` directories
- **Session Management**: `getDebit.py` handles CM2W API session management