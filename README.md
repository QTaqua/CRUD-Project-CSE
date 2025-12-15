# CRUD-Project-CSE
crud project for cs elective project
# 🥊 GAME of JAB API: Tournament Data Service

## Project Overview

This is a RESTful API built for the **GAME of JAB** league, designed to manage core tournament data, including **Teams**, **Players**, and **Matches**. This project fulfills the requirements for the CSE 1 Final Project, demonstrating a fully functional CRUD (Create, Read, Update, Delete) API, database integration with MySQL, custom formatting, and security measures.

---

## 🛠️ Prerequisites & Setup

Before running the application, ensure you have the following software installed:

1.  **Python 3.x**
2.  **MySQL Server** (and your `GAMEofJAB_db` created)
3.  **Git** (for cloning the repository)

### 1. Database Configuration

You must first set up your database using the provided SQL script.

1.  Connect to your local MySQL server.
2.  Run the full SQL script to your local machine.
3.  **Crucially:** Update the connection details in `app.py` (or a separate config file) to match your local MySQL credentials.

### 2. Local Setup

Clone the repository and set up the Python environment.

```bash
# Clone the repository
git clone https://github.com/QTaqua/CRUD-Project-CSE
cd GAMEofJAB_API

# Create and activate the virtual environment
# Windows:
# python -m venv venv
# venv\Scripts\activate.bat
# Linux/macOS:
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```
### 3. Run App
1.  Activate MySQL Server(where the database is stored)
2.  Run python app.py(ensure virtual environment is running else the program will not start)
3.  (optional) open index.html in file to show frontend for easier demonstration of the CRUD function
4.  Open the server in postman or cURL and use the routes provided in the code to run the operations.
