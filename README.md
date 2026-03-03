# 🎓 Faculty Research Impact Analysis System

A web-based research management system designed to evaluate and analyze faculty research performance using dynamic analytics, ranking algorithms, and bulk data processing.

---

## 🚀 Project Overview

Traditional faculty evaluation systems rely heavily on publication count and citation metrics. These systems often lack real-time analytics, centralized management, and advanced decision-support features.

This project introduces a secure and scalable Faculty Research Impact Analysis System that enables administrators to:

- Manage faculty records
- Add and track research publications
- Perform research impact ranking
- Upload bulk faculty data via CSV
- Visualize research analytics using dashboards

---

## 🛠️ Technologies Used

- Python
- Streamlit
- SQLite (WAL mode enabled)
- Pandas
- SHA-256 Password Encryption

---

## 🔐 Security Features

- Admin authentication
- Encrypted password storage (SHA-256)
- Role-based access (Admin only version)
- Delete confirmation safeguards
- Input validation to prevent empty records
- Ultra-stable database handling with WAL mode

---

## 📊 Features

### ✅ Admin Login
Secure login system with encrypted password validation.

### ✅ Faculty Management
- Add faculty
- Edit faculty
- Delete faculty (with confirmation)
- Search by name
- Filter by department

### ✅ Publication Management
- Add publications
- Store year, citations, impact factor

### ✅ Research Impact Ranking
Research Score Formula:
