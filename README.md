# Business-Friendly-Streamlit-App
A business-friendly Streamlit web app that translates natural language into SQL queries using NVIDIA LLMs

## 🗄️ Database

This project uses MySQL as its backend database.

The application works with the following four tables:

* student
* bridge
* chess
* music

The database table structure is provided in [`database/schema.sql`](database/schema.sql).

Database credentials and API keys are not included in this repository. They are securely managed using environment variables for local development.
