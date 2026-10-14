# Cloud-Based Student Task Manager
### University Practical Project for GMIU Practical Examination (Cloud Computing)

A full-stack, cloud-native web application designed and built for the **GMIU Cloud Computing Practical Examination**. The project demonstrates application hosting on a public cloud, serverless container compute (**Google Cloud Run**), cloud database persistence (**Google Cloud Firestore**), least-privilege security (**Google Cloud IAM & ADC**), and cloud resource management.

---

## Architecture Overview

```mermaid
flowchart LR
    A[Student Browser / Mobile] -->|HTTPS Port 443| B[Cloud Run Load Balancer / SSL Edge]
    subgraph Google Cloud Platform (Region: asia-south1 / Mumbai)
        B --> C[Cloud Run Container\nPython 3.11 + Flask + Gunicorn]
        C -->|Application Default Credentials| D[(Cloud Firestore NoSQL\nCollection: 'tasks')]
        C -.->|Stdout / Stderr| E[Cloud Logging]
        C -.->|Telemetry| F[Cloud Monitoring]
    end
```

---

## Key Features

1. **Academic Dashboard:** Real-time summary cards displaying Total Tasks, Pending Tasks, Completed Tasks, and a live Completion Rate progress bar.
2. **Task Creation Form:** Add academic tasks with Title, Course/Subject, Priority level (High, Medium, Low), Due Date, and detailed instructions.
3. **Persistent Cloud Storage:** Tasks are stored directly in **Google Cloud Firestore (Native Mode)** with timestamps, UUIDs, and completion states.
4. **Task Operations:** Mark tasks completed with visual strike-through feedback, edit existing task details, and delete tasks with confirmation dialogs.
5. **Search & Filter:** Real-time search across title/subject/description, and filtering by completion status (Pending/Completed) and Priority level.
6. **Toast Feedback System:** Instant notification toasts after each create, update, toggle, or delete operation.
7. **Cloud Health Diagnostics:** Built-in modal and live status pill reporting Cloud Run runtime info and Firestore connectivity status.
8. **Responsive Dark UI:** Curated glassmorphism design built with semantic HTML5, modern CSS3, and vanilla JavaScript that works on both mobile phones and laptops.

---

## Technology Stack

- **Frontend:** Semantic HTML5, CSS3 (Glassmorphism design tokens), Vanilla JavaScript (ES6+).
- **Backend API:** Python 3 (Flask RESTful framework).
- **WSGI Production Server:** Gunicorn (8 concurrent worker threads).
- **Containerization:** Docker (`python:3.11-slim` with unprivileged system user).
- **Cloud Compute Service:** Google Cloud Run (Serverless, auto-scaling, scale-to-zero).
- **Cloud Database:** Google Cloud Firestore (NoSQL Document Store, Native Mode).
- **Cloud Region:** `asia-south1` (Mumbai, India).

---

## File Structure

```
Cloud-Student-Task-Manager/
├── app.py                  # Main Flask application and Firestore REST API
├── requirements.txt        # Python production dependencies
├── Dockerfile              # Production multi-threaded container definition
├── .dockerignore           # Build exclusions for security and image optimization
├── .env.example            # Environment configuration template
├── START_APP.bat           # One-click Windows development launcher
├── test_app.py             # Complete unit and integration test suite
├── DEPLOYMENT_GUIDE.md     # Step-by-step Google Cloud deployment instructions
├── PRACTICAL_REPORT.md     # Full academic laboratory report for GMIU submission
├── README.md               # Project documentation (this file)
├── templates/
│   └── index.html          # Semantic HTML5 dashboard template
└── static/
    ├── css/
    │   └── style.css       # Design system and glassmorphic styling
    └── js/
        └── app.js          # Frontend controller and asynchronous API fetch logic
```

---

## Quickstart: Local Development

### 1. Prerequisites
- Python 3.10+ installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Unit Tests
```bash
python -m unittest test_app.py
```
*(All 9 tests should pass, verifying API routes, input validation, and Firestore error handling).*

### 4. Start the Application Locally
Run with Python:
```bash
python app.py
```
*Or double-click `START_APP.bat` on Windows.*

Open your browser to: [http://localhost:8080](http://localhost:8080)

> **Note on Firestore locally:** When running locally without Google Cloud credentials, the application will display a clear notification banner: `Google Cloud credentials not found.`. When deployed to Google Cloud Run, it connects automatically via Cloud Run's service identity.

---

## Google Cloud Deployment Summary

For the complete beginner-friendly deployment instructions, refer to [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

### Quick Deployment using Google Cloud Shell:
1. Open [Google Cloud Console](https://console.cloud.google.com/) and activate **Cloud Shell**.
2. Create Firestore database in Native mode (Region: `asia-south1` Mumbai).
3. Upload or navigate to the project directory and run:
   ```bash
   gcloud run deploy student-task-manager \
       --source . \
       --region asia-south1 \
       --platform managed \
       --allow-unauthenticated \
       --memory 256Mi \
       --cpu 1 \
       --min-instances 0 \
       --max-instances 2
   ```
4. Cloud Run will provide your public URL:
   `https://student-task-manager-[hash]-el.a.run.app`

---

## Resource & Cost Management

- **Scale to Zero:** `--min-instances 0` ensures containers shut down when no requests arrive, resulting in zero idle charges.
- **Max Instances Capped:** `--max-instances 2` prevents unintended autoscaling spikes.
- **Resource Limits:** `--memory 256Mi` and `--cpu 1` maintain lightweight, cost-effective execution.
- **Teardown after Viva:**
  ```bash
  gcloud run services delete student-task-manager --region asia-south1 --quiet
  ```

---

## Viva Voce Quick Review

1. **What is Google Cloud Run?**  
   A serverless compute platform that runs containerized applications on demand, automatically scaling from zero to handle incoming HTTP requests.
2. **What is Cloud Firestore?**  
   A serverless, auto-scaling NoSQL document database where data is stored in JSON-like documents organized into collections.
3. **What is the difference between Compute and Storage?**  
   Compute (Cloud Run) executes the application code and handles requests ephemerally; Storage (Firestore) persistently retains task data even when compute instances shut down.
4. **How does authentication work between Cloud Run and Firestore?**  
   Cloud Run uses **Application Default Credentials (ADC)**. The container inherits the identity of its IAM Service Account (`roles/datastore.user`), removing the need for hardcoded credentials.

---

## Academic Information

- **Institution:** Gyanmanjari Innovative University (GMIU), Bhavnagar
- **Practical:** Cloud Computing Laboratory Examination
- **Target Platform:** Google Cloud Platform (GCP)
- **Course:** B.Tech Computer Science / Information Technology
