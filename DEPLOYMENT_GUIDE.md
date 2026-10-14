# Google Cloud Run & Firestore Deployment Guide
**Project:** Cloud-Based Student Task Manager  
**Course:** Cloud Computing Laboratory (GMIU Practical Examination)  
**Target Cloud Platform:** Google Cloud Platform (GCP)  
**Target Region:** Mumbai, India (`asia-south1`)  

---

## Table of Contents
1. [Important Billing & Safety Precautions](#1-important-billing--safety-precautions)
2. [Cloud Architecture Overview](#2-cloud-architecture-overview)
3. [Prerequisites](#3-prerequisites)
4. [Step 1: Create a Google Cloud Project](#step-1-create-a-google-cloud-project)
5. [Step 2: Enable Required Google Cloud APIs](#step-2-enable-required-google-cloud-apis)
6. [Step 3: Create Firestore Database (Native Mode)](#step-3-create-firestore-database-native-mode)
7. [Step 4: Deploying to Google Cloud Run](#step-4-deploying-to-google-cloud-run)
   - [Method A: Cloud Shell Deployment (Easiest & Recommended)](#method-a-cloud-shell-deployment-recommended)
   - [Method B: Local Google Cloud CLI Deployment](#method-b-local-google-cloud-cli-deployment)
8. [Step 5: IAM Permissions & Security (Least Privilege)](#step-5-iam-permissions--security-least-privilege)
9. [Step 6: Resource Management & Cost Optimization](#step-6-resource-management--cost-optimization)
10. [Step 7: Verification & Testing in the Cloud](#step-7-verification--testing-in-the-cloud)
11. [Step 8: Monitoring Logs & Service Health](#step-8-monitoring-logs--service-health)
12. [Step 9: Resource Clean-up After Practical Exam](#step-9-resource-clean-up-after-practical-exam)

---

## 1. Important Billing & Safety Precautions

> [!IMPORTANT]
> **Billing Notice:** Google Cloud requires a billing account to deploy services like Cloud Run and Cloud Build. While Google offers a free trial ($300 credit) and generous free tier quotas, services can incur nominal charges if limits are exceeded. Always review the billing estimate before enabling paid resources.

### Safe Budgeting Rules for College Practical:
1. **Scale to Zero:** Cloud Run automatically scales to 0 instances when no requests are arriving. You only pay for CPU and memory during actual request processing (down to the nearest 100 milliseconds).
2. **Limit Max Instances:** Always set `--max-instances 2` so your service can never scale out excessively if traffic spikes.
3. **Firestore Free Tier:** Google Cloud Firestore includes 50,000 document reads, 20,000 document writes, and 20,000 document deletes per day for free under the Google Cloud Free Tier.
4. **Set a Budget Alert:** Create a $1 (₹100 INR) budget alert in the GCP Console to receive immediate email notification if any unexpected charge occurs.
5. **Clean up after examination:** Delete the Cloud Run service and Artifact Registry container images once your practical evaluation is complete.

---

## 2. Cloud Architecture Overview

```mermaid
flowchart LR
    A[Student Browser / Smartphone] -->|HTTPS Requests| B[Cloud Run Ingress / Load Balancer]
    subgraph Google Cloud Platform (asia-south1 / Mumbai)
        B --> C[Cloud Run Container\nPython 3.11 + Flask + Gunicorn]
        C -->|ADC / IAM Authentication| D[(Cloud Firestore NoSQL\nDatabase: tasks collection)]
        C -.->|Application Logs| E[Cloud Logging]
        C -.->|Metrics & Latency| F[Cloud Monitoring]
    end
```

---

## 3. Prerequisites
- A Google Account (Gmail / College GSuite ID).
- Google Cloud Console access: [https://console.cloud.google.com/](https://console.cloud.google.com/)
- An active billing account or GCP Free Trial account linked to your project.

---

## Step 1: Create a Google Cloud Project

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown at the top navigation bar and click **New Project**.
3. Enter Project Name: `gmiu-student-tasks` (or any unique name).
4. Note your **Project ID** (e.g., `gmiu-student-tasks-438910`). You will need this for deployment.
5. Click **Create** and wait for the notification banner confirming project creation.
6. Make sure your new project is selected in the top bar.

---

## Step 2: Enable Required Google Cloud APIs

Your project requires 4 Google Cloud APIs to build and run containerized serverless apps:

Open the **Cloud Shell** (terminal icon in top-right of GCP Console) or run in your terminal:
```bash
# Set your active project ID
gcloud config set project YOUR_PROJECT_ID

# Enable Cloud Run, Cloud Build, Artifact Registry, and Firestore APIs
gcloud services enable \
    run.googleapis.com \
    firestore.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com
```

*Expected output:* `Operation "operations/..." finished successfully.`

---

## Step 3: Create Firestore Database (Native Mode)

1. In the GCP Console navigation menu (top left), search for **Firestore** or go to **Databases > Firestore**.
2. Click **Create Database**.
3. Select database mode: **Firestore Native mode** (Recommended).
4. Set Database ID: `(default)`.
5. Select Location / Region:
   - Choose **asia-south1 (Mumbai)** to minimize network latency in India.
   - *(Alternatively, choose `asia-south2 (Delhi)` or `us-central1` if Mumbai is unavailable in your account tier).*
6. Secure Rules: Select **Start in production mode** or click **Create**.
7. Click **Create Database**. The database is provisioned in less than 30 seconds.

---

## Step 4: Deploying to Google Cloud Run

### Method A: Cloud Shell Deployment (Recommended)
This method is the fastest for university exams because it does not require installing Docker or Google Cloud SDK on your personal laptop.

1. In the Google Cloud Console, click the **Activate Cloud Shell** icon `[>_]` in the top right.
2. Clone or upload your project folder `Cloud-Student-Task-Manager` to Cloud Shell.
   - *Option:* Click the three dots `⋮` in Cloud Shell and select **Upload > Upload Folder / Zip**.
3. Navigate into the project folder:
   ```bash
   cd Cloud-Student-Task-Manager
   ```
4. Deploy the application to Cloud Run using a single command:
   ```bash
   gcloud run deploy student-task-manager \
       --source . \
       --region asia-south1 \
       --platform managed \
       --allow-unauthenticated \
       --memory 256Mi \
       --cpu 1 \
       --min-instances 0 \
       --max-instances 2 \
       --set-env-vars CLOUD_RUN_REGION="asia-south1 (Mumbai)"
   ```
5. Google Cloud Build will automatically build your Docker container, push it to Artifact Registry, and launch it on Cloud Run.
6. When prompted: `Do you want to continue (Y/n)?`, press `Y` and Enter.
7. Once finished, Cloud Shell will output your public HTTPS URL:
   ```
   Service [student-task-manager] revision [student-task-manager-00001-abc] has been deployed and is serving 100 percent of traffic.
   Service URL: https://student-task-manager-xxxxxxxx-el.a.run.app
   ```

---

### Method B: Local Google Cloud CLI Deployment
If you have `gcloud` installed locally:
1. Open PowerShell / Terminal in `Cloud-Student-Task-Manager`.
2. Authenticate:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
3. Deploy directly using the same command:
   ```bash
   gcloud run deploy student-task-manager \
       --source . \
       --region asia-south1 \
       --allow-unauthenticated \
       --memory 256Mi \
       --cpu 1 \
       --min-instances 0 \
       --max-instances 2
   ```

---

## Step 5: IAM Permissions & Security (Least Privilege)

Cloud Run uses a default Compute Service Account:  
`[PROJECT_NUMBER]-compute@developer.gserviceaccount.com`

By default in newly created GCP projects, this service account has sufficient Editor/Datastore permissions. To adhere to the **Principle of Least Privilege**:

1. In the GCP Console, go to **IAM & Admin > IAM**.
2. Find the runtime service account used by your Cloud Run service.
3. Ensure it only has the role:
   - **Cloud Datastore User** (`roles/datastore.user`)
4. This role allows the container to read and write to Firestore without granting administrative or billing permissions.
5. **No Secret Keys in Source Code:** Because Cloud Run uses Application Default Credentials (ADC), your code connects securely without hardcoded API keys, tokens, or passwords.

---

## Step 6: Resource Management & Cost Optimization

For university demonstrations, resource parameters should be explicitly constrained:

| Setting | Flag | Recommended Value | Explanation |
| :--- | :--- | :--- | :--- |
| **Memory** | `--memory` | `256Mi` | Flask is lightweight; 256 MB is plenty and keeps costs lowest. |
| **CPU** | `--cpu` | `1` | 1 vCPU handles student requests with microsecond latency. |
| **Min Instances**| `--min-instances` | `0` | **Scale to zero:** When nobody is browsing, 0 containers run and 0 compute cost is billed. |
| **Max Instances**| `--max-instances` | `2` | Prevents runaway auto-scaling and budget overruns. |
| **Concurrency** | `--concurrency` | `80` | Each container handles up to 80 simultaneous requests. |
| **Timeout** | `--timeout` | `60s` | Terminates hanging connections automatically. |

To update an existing deployment with these limits:
```bash
gcloud run services update student-task-manager \
    --region asia-south1 \
    --memory 256Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 2
```

---

## Step 7: Verification & Testing in the Cloud

Once your deployment finishes, verify these practical checkpoints:

1. **Open Public URL:** Open the URL provided by Cloud Run (e.g. `https://student-task-manager-xxxx.a.run.app`) on your laptop browser and on your mobile phone.
2. **Verify Header Status Pill:** Check that the top-right status pill displays:
   - `Cloud Run (Active)`
   - `Firestore: Connected`
3. **Add a Task:** Create a new task titled `"Cloud Computing Unit 4 Notes"`.
4. **Inspect Cloud Firestore:**
   - In GCP Console, open **Firestore > Databases > (default) > Data**.
   - Select the `tasks` collection.
   - Verify that your task record appears with its Title, Subject, Priority, and Timestamp.
5. **Toggle Status:** Click the checkmark to mark the task completed. Refresh the browser; the status stays completed persistently.
6. **Search & Filter:** Filter by "Pending", "Completed", or priority "High".

---

## Step 8: Monitoring Logs & Service Health

To show resource monitoring to your practical examiner:

1. In the GCP Console, navigate to **Cloud Run > Services > student-task-manager**.
2. Click the **Metrics** tab:
   - View **Request count** (shows requests per second).
   - View **Request latencies** (shows median response time in ms).
   - View **Container instance count** (shows scaling between 0 and 1-2 instances).
   - View **Container memory utilization** and **CPU utilization**.
3. Click the **Logs** tab:
   - View real-time Gunicorn access logs:
     `2026-10-14 12:45:00 [INFO] student_task_manager: Task '...' stored in Firestore.`
   - Filter logs by severity (`Default`, `Info`, `Warning`, `Error`).

---

## Step 9: Resource Clean-up After Practical Exam

After your viva examination and practical evaluation are finished, delete resources to ensure zero recurring charges:

### 1. Delete the Cloud Run Service:
```bash
gcloud run services delete student-task-manager --region asia-south1 --quiet
```

### 2. Delete Container Images in Artifact Registry:
```bash
gcloud artifacts repositories delete cloud-run-source-deploy --location asia-south1 --quiet
```

### 3. (Optional) Delete Firestore Data or Entire Project:
If this project was created exclusively for this practical exam, you can delete the entire GCP project:
```bash
gcloud projects delete YOUR_PROJECT_ID
```
Deleting the project immediately stops all billing and deletes all associated cloud resources.
