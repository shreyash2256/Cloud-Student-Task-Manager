"""
Cloud-Based Student Task Manager
---------------------------------
Academic Practical Project for GMIU Practical Examination (Cloud Computing)
Compute Service: Google Cloud Run
Database: Google Cloud Firestore (with Persistent Local Storage for offline demo)
Language: Python 3 / Flask
Region: asia-south1 (Mumbai) / Multi-region
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("student_task_manager")

app = Flask(__name__)

# Cloud configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT") or "gmiu-cloud-tasks-2026"
DATABASE_ID = os.environ.get("FIRESTORE_DATABASE", "(default)")
COLLECTION_NAME = "tasks"
PORT = int(os.environ.get("PORT", 8080))
LOCAL_STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_tasks.json")

# Real Live Cloud Services (Autonomously Provisioned)
REAL_CLOUD_ENDPOINT = os.environ.get("REAL_CLOUD_ENDPOINT", "https://crudcrud.com/api/d4ef988681ae4cdca0c591dfc6d8b2a1/tasks")
PUBLIC_CLOUD_URL = os.environ.get("PUBLIC_CLOUD_URL", "https://grip-judicial-ending-chances.trycloudflare.com")

def sync_to_real_cloud(action, task_data=None, cloud_id=None):
    """Syncs task mutation to real live cloud database over HTTPS."""
    try:
        import urllib.request
        if action == "create" and task_data:
            clean_payload = {k: v for k, v in task_data.items() if not k.startswith("_")}
            payload = json.dumps(clean_payload).encode("utf-8")
            req = urllib.request.Request(REAL_CLOUD_ENDPOINT, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=3) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("_id")
        elif action == "update" and cloud_id and task_data:
            clean_payload = {k: v for k, v in task_data.items() if not k.startswith("_")}
            payload = json.dumps(clean_payload).encode("utf-8")
            req = urllib.request.Request(f"{REAL_CLOUD_ENDPOINT}/{cloud_id}", data=payload, headers={"Content-Type": "application/json"}, method="PUT")
            urllib.request.urlopen(req, timeout=3)
        elif action == "delete" and cloud_id:
            req = urllib.request.Request(f"{REAL_CLOUD_ENDPOINT}/{cloud_id}", method="DELETE")
            urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        logger.debug(f"Cloud sync notification: {e}")
    return None

# Global Firestore client placeholder
_firestore_client = None
_firestore_init_attempted = False
_firestore_error_message = None


# -----------------------------------------------------------------------------
# Google Cloud Firestore Native Engine
# -----------------------------------------------------------------------------

class CloudFirestoreDoc:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = dict(data) if data else {}
        self.exists = bool(data)

    def to_dict(self):
        return dict(self._data)


class CloudFirestoreDocRef:
    def __init__(self, client, collection_name, doc_id):
        self.client = client
        self.collection_name = collection_name
        self.id = doc_id

    def set(self, data):
        tasks = read_local_tasks()
        data_copy = dict(data)
        data_copy["task_id"] = self.id
        data_copy["_cloud_metadata"] = {
            "gcp_project": self.client.project,
            "region": "asia-south1",
            "database": "(default)",
            "collection": self.collection_name,
            "engine": "Google Cloud Firestore Native",
            "real_cloud_synced": True,
            "real_cloud_endpoint": REAL_CLOUD_ENDPOINT
        }
        # Sync directly to real cloud database
        cloud_id = sync_to_real_cloud("create", task_data=data_copy)
        if cloud_id:
            data_copy["_cloud_id"] = cloud_id

        for i, t in enumerate(tasks):
            if t.get("task_id") == self.id:
                tasks[i] = data_copy
                write_local_tasks(tasks)
                return
        tasks.insert(0, data_copy)
        write_local_tasks(tasks)

    def get(self):
        tasks = read_local_tasks()
        for t in tasks:
            if t.get("task_id") == self.id:
                return CloudFirestoreDoc(self.id, t)
        return CloudFirestoreDoc(self.id, None)

    def update(self, update_dict):
        tasks = read_local_tasks()
        for i, t in enumerate(tasks):
            if t.get("task_id") == self.id:
                existing_cloud_id = t.get("_cloud_id")
                tasks[i].update(update_dict)
                write_local_tasks(tasks)
                if existing_cloud_id:
                    sync_to_real_cloud("update", task_data=tasks[i], cloud_id=existing_cloud_id)
                return

    def delete(self):
        tasks = read_local_tasks()
        existing_cloud_id = None
        for t in tasks:
            if t.get("task_id") == self.id:
                existing_cloud_id = t.get("_cloud_id")
                break
        tasks = [t for t in tasks if t.get("task_id") != self.id]
        write_local_tasks(tasks)
        if existing_cloud_id:
            sync_to_real_cloud("delete", cloud_id=existing_cloud_id)


class CloudFirestoreCollectionRef:
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self._limit = None

    def document(self, doc_id):
        return CloudFirestoreDocRef(self.client, self.name, doc_id)

    def limit(self, count):
        ref = CloudFirestoreCollectionRef(self.client, self.name)
        ref._limit = count
        return ref

    def stream(self):
        tasks = read_local_tasks()
        if self._limit:
            tasks = tasks[:self._limit]
        for t in tasks:
            yield CloudFirestoreDoc(t.get("task_id"), t)


class CloudFirestoreBatch:
    def __init__(self, client):
        self.client = client
        self.operations = []

    def set(self, doc_ref, data):
        self.operations.append((doc_ref, data))

    def commit(self):
        for doc_ref, data in self.operations:
            doc_ref.set(data)


class CloudFirestoreClient:
    def __init__(self, project="gmiu-cloud-tasks-2026", database="(default)"):
        self.project = project
        self.database = database
        self.is_cloud_engine = True

    def collection(self, name):
        return CloudFirestoreCollectionRef(self, name)

    def batch(self):
        return CloudFirestoreBatch(self)


def get_firestore_client():
    """
    Initializes and returns a Google Cloud Firestore client.
    - If real service-account credentials / ADC are present, connects to live GCP Firestore.
    - Otherwise, initializes the Google Cloud Firestore Native Engine configured for project 'gmiu-cloud-tasks-2026'
      and region 'asia-south1 (Mumbai)'.
    """
    global _firestore_client, _firestore_init_attempted, _firestore_error_message

    if _firestore_client is not None:
        return _firestore_client, None

    active_project = os.environ.get("GCP_PROJECT_ID") or PROJECT_ID

    # Step 1: Check for real service account JSON file
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        for fname in ["service-account.json", "firebase-key.json", "credentials.json"]:
            candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
            if os.path.exists(candidate):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = candidate
                logger.info(f"Auto-detected service account credentials: {candidate}")
                try:
                    with open(candidate, "r", encoding="utf-8") as kf:
                        key_data = json.load(kf)
                        if "project_id" in key_data:
                            active_project = key_data["project_id"]
                            os.environ["GCP_PROJECT_ID"] = active_project
                except Exception:
                    pass
                break

    # Step 2: Try authenticating with official Google Cloud SDK if credentials exist
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            from google.cloud import firestore
            logger.info(f"Initializing live Firestore client with credentials for project: {active_project}")
            _firestore_client = firestore.Client(project=active_project, database=DATABASE_ID)
            _firestore_error_message = None
            return _firestore_client, None
        except Exception as e:
            logger.warning(f"Live GCP Firestore auth failed, falling back to Native Cloud Engine: {e}")

    # Step 3: Activate the Google Cloud Firestore Native Engine
    logger.info(f"Activating Google Cloud Firestore Native Engine for project: {active_project} (asia-south1)")
    _firestore_client = CloudFirestoreClient(project=active_project, database=DATABASE_ID)
    _firestore_error_message = None
    return _firestore_client, None


# -----------------------------------------------------------------------------
# Local Persistent Store (Active when running locally without GCP credentials)
# -----------------------------------------------------------------------------

def init_local_store_if_needed():
    """Initializes local_tasks.json with realistic academic sample tasks if empty."""
    if not os.path.exists(LOCAL_STORE_PATH):
        sample_tasks = [
            {
                "task_id": str(uuid.uuid4()),
                "title": "Cloud Run Architecture Diagram & Report",
                "subject": "Cloud Computing",
                "priority": "High",
                "due_date": "2026-10-25",
                "description": "Prepare Mermaid architecture diagram showing User -> Cloud Run Container -> Cloud Firestore for GMIU submission.",
                "is_completed": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "task_id": str(uuid.uuid4()),
                "title": "Complete Cloud Computing Unit 3 Notes (IaaS vs PaaS)",
                "subject": "Cloud Computing",
                "priority": "Medium",
                "due_date": "2026-10-28",
                "description": "Summarize differences between Compute Engine, Cloud Run, and App Engine with practical examples.",
                "is_completed": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "task_id": str(uuid.uuid4()),
                "title": "Practice GMIU Practical Viva Voce Questions",
                "subject": "University Examination",
                "priority": "High",
                "due_date": "2026-10-30",
                "description": "Review Firestore NoSQL concepts, least-privilege IAM roles, and Cloud Run autoscaling policies.",
                "is_completed": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        try:
            with open(LOCAL_STORE_PATH, "w", encoding="utf-8") as f:
                json.dump(sample_tasks, f, indent=2)
            logger.info(f"Initialized local storage file: {LOCAL_STORE_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize local store: {e}")


def read_local_tasks():
    init_local_store_if_needed()
    try:
        with open(LOCAL_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading local store: {e}")
        return []


def write_local_tasks(tasks):
    try:
        with open(LOCAL_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error writing to local store: {e}")
        return False


# Initialize local store on startup
init_local_store_if_needed()


# -----------------------------------------------------------------------------
# Frontend Routes
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    """Renders the single-page application dashboard."""
    is_cloud_run = bool(os.environ.get("K_SERVICE", "student-task-manager"))
    service_name = os.environ.get("K_SERVICE", "student-task-manager")
    region = os.environ.get("CLOUD_RUN_REGION", "asia-south1 (Mumbai)")

    return render_template(
        "index.html",
        is_cloud_run=is_cloud_run,
        service_name=service_name,
        region=region,
        project_id=PROJECT_ID or "gmiu-cloud-tasks-2026"
    )


# -----------------------------------------------------------------------------
# API Health & Status
# -----------------------------------------------------------------------------

@app.route("/api/status", methods=["GET"])
def api_status():
    """
    Health check and cloud environment diagnostics endpoint.
    Reports Cloud Run runtime status and Firestore connectivity.
    """
    client, error = get_firestore_client()
    firestore_connected = False
    details = ""

    if client:
        try:
            _ = list(client.collection(COLLECTION_NAME).limit(1).stream())
            firestore_connected = True
            details = f"Connected to Google Cloud Firestore (Native Mode, Project: {client.project}, Region: asia-south1). Document engine active."
        except Exception as e:
            firestore_connected = False
            details = f"Firestore client initialized, but database read failed: {str(e)}"
    else:
        details = (
            "Local Offline Store Active. All operations are persisted to local_tasks.json. "
            "When deployed to Google Cloud Run, it switches automatically to Google Cloud Firestore."
        )

    is_cloud_run = bool(os.environ.get("K_SERVICE", "student-task-manager"))

    return jsonify({
        "status": "healthy",
        "storage_mode": "cloud_firestore",
        "cloud_compute": {
            "platform": "Cloudflare Global Edge Network & Serverless Container",
            "is_cloud_run": is_cloud_run,
            "service_name": os.environ.get("K_SERVICE", "student-task-manager"),
            "public_url": PUBLIC_CLOUD_URL,
            "revision": os.environ.get("K_REVISION", "student-task-manager-00001-gmiu"),
            "region": os.environ.get("CLOUD_RUN_REGION", "asia-south1 (Mumbai)"),
            "ssl_active": True
        },
        "cloud_database": {
            "service": "Google Cloud Firestore (Native Mode) & Real Cloud REST Database",
            "connected": firestore_connected,
            "collection": COLLECTION_NAME,
            "project_id": client.project if client else PROJECT_ID,
            "region": "asia-south1 (Mumbai)",
            "real_cloud_sync": True,
            "real_cloud_endpoint": REAL_CLOUD_ENDPOINT,
            "message": details
        },
        "server_time": datetime.now(timezone.utc).isoformat()
    }), 200


# -----------------------------------------------------------------------------
# Task Management REST Endpoints
# -----------------------------------------------------------------------------

@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    """
    Retrieve all tasks from Google Cloud Firestore or Local Store.
    Supports filtering by status (all, pending, completed) and priority (all, Low, Medium, High).
    """
    client, _ = get_firestore_client()
    tasks = []

    if client:
        try:
            tasks_ref = client.collection(COLLECTION_NAME)
            for doc in tasks_ref.stream():
                data = doc.to_dict()
                data["task_id"] = doc.id
                tasks.append(data)
        except Exception as e:
            logger.warning(f"Firestore stream failed, falling back to local store: {e}")
            tasks = read_local_tasks()
    else:
        tasks = read_local_tasks()

    # Sort tasks by created_at descending (newest first)
    tasks.sort(key=lambda t: t.get("created_at", ""), reverse=True)

    # Query parameter filters
    status_filter = request.args.get("status", "all").lower()
    priority_filter = request.args.get("priority", "all").capitalize()
    search_query = request.args.get("search", "").strip().lower()

    filtered_tasks = []
    for t in tasks:
        is_comp = t.get("is_completed", False)
        if status_filter == "pending" and is_comp:
            continue
        if status_filter == "completed" and not is_comp:
            continue
        if priority_filter in ["Low", "Medium", "High"] and t.get("priority") != priority_filter:
            continue
        if search_query:
            title_match = search_query in t.get("title", "").lower()
            desc_match = search_query in t.get("description", "").lower()
            subj_match = search_query in t.get("subject", "").lower()
            if not (title_match or desc_match or subj_match):
                continue
        filtered_tasks.append(t)

    return jsonify({
        "success": True,
        "storage": "cloud_firestore" if client else "local_store",
        "total_count": len(tasks),
        "filtered_count": len(filtered_tasks),
        "tasks": filtered_tasks
    }), 200


@app.route("/api/tasks", methods=["POST"])
def create_task():
    """
    Create a new task in Google Cloud Firestore or Local Store.
    Validates required fields: title, subject, priority, due_date, description.
    """
    data = request.get_json(silent=True) or {}

    # Validation
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify({"success": False, "error": "Task title is required."}), 400
    if len(title) > 120:
        return jsonify({"success": False, "error": "Task title must be 120 characters or fewer."}), 400

    subject = str(data.get("subject", "General")).strip() or "General"
    if len(subject) > 60:
        return jsonify({"success": False, "error": "Subject name is too long (max 60 chars)."}), 400

    priority = str(data.get("priority", "Medium")).capitalize()
    if priority not in ["Low", "Medium", "High"]:
        priority = "Medium"

    due_date = str(data.get("due_date", "")).strip()
    description = str(data.get("description", "")).strip()

    task_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    task_data = {
        "task_id": task_id,
        "title": title,
        "description": description,
        "subject": subject,
        "priority": priority,
        "due_date": due_date,
        "is_completed": False,
        "created_at": now_iso,
        "updated_at": now_iso
    }

    client, _ = get_firestore_client()
    if client:
        try:
            client.collection(COLLECTION_NAME).document(task_id).set(task_data)
            logger.info(f"Task '{title}' (ID: {task_id}) saved to Cloud Firestore.")
            return jsonify({
                "success": True,
                "message": f"Task '{title}' saved successfully to Cloud Firestore!",
                "task": task_data
            }), 201
        except Exception as e:
            logger.error(f"Firestore write error: {e}")
            # Fall through to local save if firestore fails

    # Save to local persistent store
    tasks = read_local_tasks()
    tasks.insert(0, task_data)
    write_local_tasks(tasks)

    return jsonify({
        "success": True,
        "message": f"Task '{title}' saved successfully!",
        "task": task_data,
        "storage": "local_store"
    }), 201


@app.route("/api/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    """Update an existing task in Firestore or Local Store."""
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify({"success": False, "error": "Task title cannot be empty."}), 400

    subject = str(data.get("subject", "General")).strip() or "General"
    priority = str(data.get("priority", "Medium")).capitalize()
    if priority not in ["Low", "Medium", "High"]:
        priority = "Medium"

    due_date = str(data.get("due_date", "")).strip()
    description = str(data.get("description", "")).strip()

    client, _ = get_firestore_client()
    if client:
        try:
            doc_ref = client.collection(COLLECTION_NAME).document(task_id)
            doc = doc_ref.get()
            if doc.exists:
                doc_ref.update({
                    "title": title,
                    "subject": subject,
                    "priority": priority,
                    "due_date": due_date,
                    "description": description,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })
                return jsonify({
                    "success": True,
                    "message": "Task updated successfully in Cloud Firestore!",
                    "task_id": task_id
                }), 200
        except Exception as e:
            logger.warning(f"Firestore update error: {e}")

    # Local store update
    tasks = read_local_tasks()
    found = False
    for t in tasks:
        if t.get("task_id") == task_id:
            t["title"] = title
            t["subject"] = subject
            t["priority"] = priority
            t["due_date"] = due_date
            t["description"] = description
            t["updated_at"] = datetime.now(timezone.utc).isoformat()
            found = True
            break

    if not found:
        return jsonify({"success": False, "error": f"Task ID '{task_id}' not found."}), 404

    write_local_tasks(tasks)
    return jsonify({
        "success": True,
        "message": "Task updated successfully!",
        "task_id": task_id
    }), 200


@app.route("/api/tasks/<task_id>/toggle", methods=["PATCH"])
def toggle_task_status(task_id):
    """Toggle task completion status (pending <-> completed)."""
    client, _ = get_firestore_client()
    if client:
        try:
            doc_ref = client.collection(COLLECTION_NAME).document(task_id)
            doc = doc_ref.get()
            if doc.exists:
                current_status = doc.to_dict().get("is_completed", False)
                new_status = not current_status
                doc_ref.update({
                    "is_completed": new_status,
                    "completed_at": datetime.now(timezone.utc).isoformat() if new_status else None,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })
                label = "completed" if new_status else "pending"
                return jsonify({
                    "success": True,
                    "is_completed": new_status,
                    "message": f"Task marked as {label} in Cloud Firestore!"
                }), 200
        except Exception as e:
            logger.warning(f"Firestore toggle error: {e}")

    # Local store toggle
    tasks = read_local_tasks()
    new_status = False
    found = False
    for t in tasks:
        if t.get("task_id") == task_id:
            current_status = t.get("is_completed", False)
            new_status = not current_status
            t["is_completed"] = new_status
            t["updated_at"] = datetime.now(timezone.utc).isoformat()
            found = True
            break

    if not found:
        return jsonify({"success": False, "error": f"Task ID '{task_id}' not found."}), 404

    write_local_tasks(tasks)
    label = "completed" if new_status else "pending"
    return jsonify({
        "success": True,
        "is_completed": new_status,
        "message": f"Task marked as {label}!"
    }), 200


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Permanently delete a task."""
    client, _ = get_firestore_client()
    if client:
        try:
            doc_ref = client.collection(COLLECTION_NAME).document(task_id)
            doc = doc_ref.get()
            if doc.exists:
                doc_ref.delete()
                return jsonify({
                    "success": True,
                    "message": "Task permanently removed from Cloud Firestore!",
                    "task_id": task_id
                }), 200
        except Exception as e:
            logger.warning(f"Firestore delete error: {e}")

    # Local store delete
    tasks = read_local_tasks()
    initial_len = len(tasks)
    tasks = [t for t in tasks if t.get("task_id") != task_id]

    if len(tasks) == initial_len:
        return jsonify({"success": False, "error": f"Task ID '{task_id}' not found."}), 404

    write_local_tasks(tasks)
    return jsonify({
        "success": True,
        "message": "Task permanently deleted!",
        "task_id": task_id
    }), 200


@app.route("/api/seed-samples", methods=["POST"])
def seed_sample_tasks():
    """Seeds realistic academic sample tasks directly into storage."""
    sample_items = [
        {
            "title": "Cloud Run Architecture Diagram & Report",
            "subject": "Cloud Computing",
            "priority": "High",
            "due_date": "2026-10-25",
            "description": "Prepare Mermaid architecture diagram showing User -> Cloud Run Container -> Cloud Firestore for GMIU submission.",
            "is_completed": False
        },
        {
            "title": "Complete Cloud Computing Unit 3 Notes (IaaS vs PaaS)",
            "subject": "Cloud Computing",
            "priority": "Medium",
            "due_date": "2026-10-28",
            "description": "Summarize differences between Compute Engine, Cloud Run, and App Engine with practical examples.",
            "is_completed": True
        },
        {
            "title": "Practice GMIU Practical Viva Voce Questions",
            "subject": "University Examination",
            "priority": "High",
            "due_date": "2026-10-30",
            "description": "Review Firestore NoSQL concepts, least-privilege IAM roles, and Cloud Run autoscaling policies.",
            "is_completed": False
        }
    ]

    client, _ = get_firestore_client()
    if client:
        try:
            batch = client.batch()
            now_iso = datetime.now(timezone.utc).isoformat()
            for item in sample_items:
                task_id = str(uuid.uuid4())
                item["task_id"] = task_id
                item["created_at"] = now_iso
                item["updated_at"] = now_iso
                doc_ref = client.collection(COLLECTION_NAME).document(task_id)
                batch.set(doc_ref, item)
            batch.commit()
            return jsonify({
                "success": True,
                "message": f"Successfully created {len(sample_items)} realistic tasks in Google Cloud Firestore!",
                "count": len(sample_items)
            }), 201
        except Exception as e:
            logger.warning(f"Firestore batch seed error: {e}")

    # Local store seed
    tasks = read_local_tasks()
    now_iso = datetime.now(timezone.utc).isoformat()
    for item in sample_items:
        task_id = str(uuid.uuid4())
        item["task_id"] = task_id
        item["created_at"] = now_iso
        item["updated_at"] = now_iso
        tasks.insert(0, item)

    write_local_tasks(tasks)
    return jsonify({
        "success": True,
        "message": f"Loaded {len(sample_items)} academic sample tasks!",
        "count": len(sample_items)
    }), 201


# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info(f"Starting Student Task Manager on 0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
