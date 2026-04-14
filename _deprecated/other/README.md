# 📊 Smart Sales Performance Dashboard

A premium Streamlit-based analytics tool designed to transform raw sales data (Excel/CSV) into actionable category-wise insights with automated product classification.

## 🚀 Features

- **Smart Column Detection**: Automatically identifies Product Name, Price, and Quantity columns using exact and partial matching.
- **Automated Categorization**: Intelligently groups products into categories like *Jeans, Polo, Panjabi, Joggers, Sweaters*, and more based on keywords.
- **Sleeve Length Logic**: Automatically differentiates between Full Sleeve (FS) and Half Sleeve (HS) for Shirts and T-Shirts.
- **Interactive Visualizations**: 
  - Revenue Share (Donut Chart)
  - Sales Volume by Category (Multi-colored Bar Chart)
- **Deep-Dive Analytics**:
  - Category-wise sales distribution.
  - Top 20 best-selling products ranking.
  - Price-point drilldown analysis.
- **Feedback & Error Tracking**: Built-in system to log misclassified items and technical errors for continuous improvement.
- **Professional Export**: Download comprehensive reports as multi-sheet Excel files.

## 🛠️ Tech Stack

- **Python 3.x**
- **Streamlit** (UI Framework)
- **Pandas** (Data Processing)
- **Plotly** (Interactive Charts)
- **XlsxWriter** (Excel Export)

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Product-Report
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🏃 Quick Start

1. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

2. Upload your sales data (Excel `.xlsx` or CSV `.csv`).
3. Verify the **Column Mapping** (the app guesses these automatically).
4. Click **Generate Dashboard** to view your analytics.
5. Use the sidebar to report any classification errors or provide feedback.

## 📂 Project Structure

- `app.py`: Main application logic and UI.
- `requirements.txt`: List of Python dependencies.
- `feedback/`: Directory containing system logs and user feedback JSON files.
- `.gitignore`: Standard rules to exclude temporary and data files.

---
*Developed for efficient sales reporting and product performance analysis.*
