# DataGuardian — Intelligent Personal Data Leak Monitor

A project designed to automatically detect **sensitive personal data** (such as CPF, email, passwords, etc.) in files like **CSV, JSON, TXT, and SQL dumps**, helping in the proactive identification of potential data leaks.

## 🔍 Key Features

- [x] File upload support (CSV, JSON, TXT, SQL)
- [x] Automatic detection of sensitive data using **Regex + NLP**
- [x] Identification of suspicious patterns (e.g. passwords in logs, exposed keys)
- [x] Interactive dashboard with risk visualization
- [ ] Email alert system *(in development)*
- [ ] Automatic encryption of critical fields *(in development)*

## ⚙️ Technologies Used

- **Python 3.9+**
- **Streamlit** – Interactive UI framework
- **Pandas** – Data processing and analysis
- **spaCy** – Natural Language Processing for contextual detection
- **Fernet (Cryptography)** – Secure field encryption
- **Regex** – Pattern-based data detection

## 🧪 Detected Sensitive Data Types

The system can automatically identify the following types of sensitive information:

| Data Type         | Example                      |
|-------------------|------------------------------|
| CPF               | 123.456.789-09               |
| CNPJ              | 12.345.678/0001-90           |
| Email             | usuario@email.com            |
| Password          | A1b@3456                     |
| Phone Number      | (11) 99999-9999              |
| Credit Card       | 5555 4444 3333 2222          |

Detection combines regular expressions with advanced Natural Language Processing (NLP), ensuring high accuracy even on unstructured text.

## 📦 How to Run the Project

#

### 1. Clone the repository

  ```bash
git clone https://github.com/RafaFelisberto/DataGuardian.git 
cd DataGuardian
  ```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```
### 3. Run the application

```bash
streamlit run app.py
```
## 🛡️ Security Goal

DataGuardian is built to help companies and information security professionals quickly identify and mitigate issues that could lead to exposure of sensitive data, aiding compliance with regulations such as **LGPD** and **GDPR**.

## 🤝 Contribution

Contributions are welcome! If you'd like to improve any part of the project, add new detection patterns, or implement pending features (like automatic encryption or email alerts), feel free to open a PR or issue on GitHub.

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details
## 🚀 New: CLI + API

### CLI (scan file/folder)
```bash
python -m cli.main scan ./samples --out reports/report.json
```

### API (FastAPI)
```bash
uvicorn api.main:app --reload
```

- `POST /scan/file?format=json|html`
- `POST /scan/text`

## 📄 Reports
DataGuardian exports:
- JSON (machine-friendly)
- HTML (audit-friendly)

Reports never include raw sensitive values (only masked previews).
