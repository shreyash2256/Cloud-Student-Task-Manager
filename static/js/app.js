/**
 * Cloud-Based Student Task Manager
 * Frontend Application Controller
 * Academic Practical Project for GMIU Practical Examination
 */

document.addEventListener('DOMContentLoaded', () => {
    // Application State
    const state = {
        tasks: [],
        filters: {
            status: 'all',
            priority: 'all',
            search: ''
        },
        cloudStatus: {
            is_cloud_run: false,
            firestore_connected: false,
            message: ''
        },
        editingTaskId: null,
        deletingTaskId: null,
        isLoading: false
    };

    // DOM Elements Cache
    const elements = {
        // Status & Alerts
        computeStatusPill: document.getElementById('computeStatusPill'),
        databaseStatusPill: document.getElementById('databaseStatusPill'),
        dbStatusDot: document.getElementById('dbStatusDot'),
        dbStatusText: document.getElementById('dbStatusText'),
        firestoreAlertBanner: document.getElementById('firestoreAlertBanner'),
        firestoreAlertDetails: document.getElementById('firestoreAlertDetails'),
        retryConnectionBtn: document.getElementById('retryConnectionBtn'),
        showSetupHelpBtn: document.getElementById('showSetupHelpBtn'),
        dismissAlertBtn: document.getElementById('dismissAlertBtn'),

        // Stats
        statTotalCount: document.getElementById('statTotalCount'),
        statPendingCount: document.getElementById('statPendingCount'),
        statCompletedCount: document.getElementById('statCompletedCount'),
        statProgressPercentage: document.getElementById('statProgressPercentage'),
        statProgressBar: document.getElementById('statProgressBar'),

        // Controls
        searchInput: document.getElementById('searchInput'),
        clearSearchBtn: document.getElementById('clearSearchBtn'),
        statusFilter: document.getElementById('statusFilter'),
        priorityFilter: document.getElementById('priorityFilter'),
        openAddTaskModalBtn: document.getElementById('openAddTaskModalBtn'),
        seedSamplesBtn: document.getElementById('seedSamplesBtn'),

        // Tasks List & States
        tasksGrid: document.getElementById('tasksGrid'),
        loadingState: document.getElementById('loadingState'),
        emptyState: document.getElementById('emptyState'),
        emptyStateDesc: document.getElementById('emptyStateDesc'),
        emptyStateCreateBtn: document.getElementById('emptyStateCreateBtn'),
        filteredCountBadge: document.getElementById('filteredCountBadge'),

        // Task Modal
        taskModal: document.getElementById('taskModal'),
        modalTitle: document.getElementById('modalTitle'),
        taskForm: document.getElementById('taskForm'),
        taskIdInput: document.getElementById('taskIdInput'),
        taskTitleInput: document.getElementById('taskTitleInput'),
        taskSubjectInput: document.getElementById('taskSubjectInput'),
        taskPriorityInput: document.getElementById('taskPriorityInput'),
        taskDueDateInput: document.getElementById('taskDueDateInput'),
        taskDescriptionInput: document.getElementById('taskDescriptionInput'),
        submitTaskBtn: document.getElementById('submitTaskBtn'),
        submitBtnText: document.getElementById('submitBtnText'),
        submitBtnSpinner: document.getElementById('submitBtnSpinner'),
        closeModalBtn: document.getElementById('closeModalBtn'),
        cancelModalBtn: document.getElementById('cancelModalBtn'),

        // Delete Modal
        deleteModal: document.getElementById('deleteModal'),
        deleteTaskTitlePreview: document.getElementById('deleteTaskTitlePreview'),
        confirmDeleteBtn: document.getElementById('confirmDeleteBtn'),
        cancelDeleteBtn: document.getElementById('cancelDeleteBtn'),
        closeDeleteModalBtn: document.getElementById('closeDeleteModalBtn'),
        deleteSpinner: document.getElementById('deleteSpinner'),

        // Diagnostics Modal
        diagnosticsBtn: document.getElementById('diagnosticsBtn'),
        diagnosticsModal: document.getElementById('diagnosticsModal'),
        closeDiagModalBtn: document.getElementById('closeDiagModalBtn'),
        closeDiagBtn: document.getElementById('closeDiagBtn'),
        diagDbMessage: document.getElementById('diagDbMessage'),

        // Setup Help Modal
        setupHelpModal: document.getElementById('setupHelpModal'),
        closeSetupHelpBtn: document.getElementById('closeSetupHelpBtn'),
        closeSetupBtn: document.getElementById('closeSetupBtn'),

        // Toast Container
        toastContainer: document.getElementById('toastContainer')
    };

    // -------------------------------------------------------------------------
    // Utilities
    // -------------------------------------------------------------------------

    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    function formatDate(dateStr) {
        if (!dateStr) return null;
        try {
            const parts = dateStr.split('-');
            if (parts.length === 3) {
                const year = parseInt(parts[0], 10);
                const month = parseInt(parts[1], 10) - 1;
                const day = parseInt(parts[2], 10);
                const d = new Date(year, month, day);
                return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            }
            return dateStr;
        } catch {
            return dateStr;
        }
    }

    function isOverdue(dateStr) {
        if (!dateStr) return false;
        try {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const due = new Date(dateStr);
            return due < today;
        } catch {
            return false;
        }
    }

    function showToast(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        let iconSvg = '';
        if (type === 'success') {
            iconSvg = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`;
        } else if (type === 'error') {
            iconSvg = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`;
        } else {
            iconSvg = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
        }

        toast.innerHTML = `
            <div class="toast-icon">${iconSvg}</div>
            <div class="toast-message">${escapeHtml(message)}</div>
        `;

        elements.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(15px)';
            setTimeout(() => toast.remove(), 250);
        }, duration);
    }

    // -------------------------------------------------------------------------
    // Cloud Diagnostics & Status
    // -------------------------------------------------------------------------

    async function checkCloudStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            state.cloudStatus.is_cloud_run = data.cloud_compute?.is_cloud_run || false;
            state.cloudStatus.firestore_connected = data.cloud_database?.connected || false;
            state.cloudStatus.message = data.cloud_database?.message || '';
            state.cloudStatus.storage_mode = data.storage_mode || 'local_store';

            // Update Database Pill
            if (state.cloudStatus.firestore_connected) {
                elements.dbStatusDot.className = 'pill-dot pill-dot-green';
                elements.dbStatusText.textContent = 'Cloud Firestore: Connected (Live)';
                elements.firestoreAlertBanner.classList.add('hidden');
            } else {
                elements.dbStatusDot.className = 'pill-dot pill-dot-amber';
                elements.dbStatusText.textContent = 'Storage: Local Persistent File';
                elements.firestoreAlertBanner.classList.remove('hidden');
                
                const alertTitle = elements.firestoreAlertBanner.querySelector('.alert-title');
                if (alertTitle) alertTitle.textContent = 'Local Development Mode Active (Offline Storage)';
                elements.firestoreAlertDetails.textContent = 
                    'Running locally with persistent storage (local_tasks.json). You can create, edit, delete, and test your student tasks right now! When deployed to Google Cloud Run, it connects to Google Cloud Firestore automatically.';
            }

            // Update Diagnostics details
            if (elements.diagDbMessage) {
                elements.diagDbMessage.textContent = JSON.stringify(data, null, 2);
            }

            return state.cloudStatus.firestore_connected;
        } catch (err) {
            elements.dbStatusDot.className = 'pill-dot pill-dot-red';
            elements.dbStatusText.textContent = 'API Offline';
            elements.firestoreAlertBanner.classList.remove('hidden');
            elements.firestoreAlertDetails.textContent = 'Cannot reach backend server. Please verify Flask application is running.';
            return false;
        }
    }

    // -------------------------------------------------------------------------
    // Tasks Operations (CRUD)
    // -------------------------------------------------------------------------

    async function fetchTasks() {
        state.isLoading = true;
        elements.loadingState.classList.remove('hidden');
        elements.emptyState.classList.add('hidden');
        elements.tasksGrid.innerHTML = '';

        try {
            const queryParams = new URLSearchParams({
                status: state.filters.status,
                priority: state.filters.priority,
                search: state.filters.search
            });

            const response = await fetch(`/api/tasks?${queryParams.toString()}`);
            const data = await response.json();

            if (response.ok && data.success) {
                state.tasks = data.tasks || [];
                updateStats(data.total_count, state.tasks);
                renderTasks();
            } else {
                elements.loadingState.classList.add('hidden');
                elements.emptyState.classList.remove('hidden');
                elements.emptyStateDesc.textContent = data.details || data.error || 'Failed to load tasks.';
                showToast(data.error || 'Failed to load tasks from Cloud Firestore', 'error');
            }
        } catch (err) {
            elements.loadingState.classList.add('hidden');
            elements.emptyState.classList.remove('hidden');
            elements.emptyStateDesc.textContent = 'Connection error while communicating with Flask backend.';
            showToast('Network error while fetching tasks', 'error');
        } finally {
            state.isLoading = false;
        }
    }

    function updateStats(totalInDb, filteredTasks) {
        // Count statuses across all fetched tasks
        let total = totalInDb;
        let pending = 0;
        let completed = 0;

        // If filtered list is identical to total, count directly
        if (state.filters.status === 'all' && state.filters.priority === 'all' && !state.filters.search) {
            total = state.tasks.length;
            pending = state.tasks.filter(t => !t.is_completed).length;
            completed = state.tasks.filter(t => t.is_completed).length;
        } else {
            // Count from currently loaded records
            pending = state.tasks.filter(t => !t.is_completed).length;
            completed = state.tasks.filter(t => t.is_completed).length;
        }

        elements.statTotalCount.textContent = total;
        elements.statPendingCount.textContent = pending;
        elements.statCompletedCount.textContent = completed;

        const rate = total > 0 ? Math.round((completed / total) * 100) : 0;
        elements.statProgressPercentage.textContent = `${rate}%`;
        elements.statProgressBar.style.width = `${rate}%`;

        elements.filteredCountBadge.textContent = `${filteredTasks.length} ${filteredTasks.length === 1 ? 'task' : 'tasks'}`;
    }

    function renderTasks() {
        elements.loadingState.classList.add('hidden');

        if (state.tasks.length === 0) {
            elements.emptyState.classList.remove('hidden');
            if (state.filters.search || state.filters.status !== 'all' || state.filters.priority !== 'all') {
                elements.emptyStateDesc.textContent = 'No tasks matched your search or filter criteria. Try resetting filters.';
            } else {
                elements.emptyStateDesc.textContent = 'No tasks found in Cloud Firestore. Click "Add New Task" to create one!';
            }
            return;
        }

        elements.emptyState.classList.add('hidden');
        elements.tasksGrid.innerHTML = '';

        state.tasks.forEach(task => {
            const card = document.createElement('article');
            card.className = `task-card task-priority-${escapeHtml(task.priority)} ${task.is_completed ? 'task-completed' : ''}`;
            card.dataset.id = task.task_id;

            const formattedDue = formatDate(task.due_date);
            const overdue = !task.is_completed && isOverdue(task.due_date);

            let createdDisplay = 'Just now';
            if (task.created_at) {
                try {
                    const createdDate = new Date(task.created_at);
                    createdDisplay = createdDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                } catch {
                    createdDisplay = '';
                }
            }

            card.innerHTML = `
                <div class="task-top">
                    <button class="task-toggle-btn" title="${task.is_completed ? 'Mark as pending' : 'Mark as completed'}" aria-label="Toggle completion">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="3">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                    </button>
                    <div class="task-details">
                        <h3 class="task-title">${escapeHtml(task.title)}</h3>
                        ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ''}
                        <div class="task-meta-row">
                            <span class="badge badge-subject">
                                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/></svg>
                                ${escapeHtml(task.subject || 'General')}
                            </span>
                            <span class="badge badge-priority-${escapeHtml(task.priority)}">
                                ${escapeHtml(task.priority)} Priority
                            </span>
                            ${formattedDue ? `
                                <span class="badge badge-date ${overdue ? 'overdue' : ''}">
                                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="4" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                                    ${overdue ? 'Overdue: ' : 'Due: '}${formattedDue}
                                </span>
                            ` : ''}
                        </div>
                    </div>
                </div>
                <div class="task-bottom">
                    <span class="task-created-time">Created: ${createdDisplay}</span>
                    <div class="task-action-btns">
                        <button class="task-action-btn edit-task-btn" title="Edit Task" aria-label="Edit Task">
                            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                            </svg>
                        </button>
                        <button class="task-action-btn delete-btn delete-task-btn" title="Delete Task" aria-label="Delete Task">
                            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;

            // Attach individual card event handlers
            const toggleBtn = card.querySelector('.task-toggle-btn');
            toggleBtn.addEventListener('click', () => toggleTaskStatus(task.task_id));

            const editBtn = card.querySelector('.edit-task-btn');
            editBtn.addEventListener('click', () => openEditModal(task));

            const deleteBtn = card.querySelector('.delete-task-btn');
            deleteBtn.addEventListener('click', () => openDeleteModal(task));

            elements.tasksGrid.appendChild(card);
        });
    }

    // Toggle Task Completion
    async function toggleTaskStatus(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/toggle`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();

            if (response.ok && data.success) {
                showToast(data.message, 'success');
                // Refresh list to update counters and styling
                fetchTasks();
            } else {
                showToast(data.error || 'Failed to toggle status', 'error');
            }
        } catch (err) {
            showToast('Network error while toggling task status', 'error');
        }
    }

    // Open Add Modal
    function openAddModal() {
        state.editingTaskId = null;
        elements.modalTitle.textContent = 'Add New Task';
        elements.submitBtnText.textContent = 'Save to Cloud Firestore';
        elements.taskIdInput.value = '';
        elements.taskTitleInput.value = '';
        elements.taskSubjectInput.value = 'Cloud Computing';
        elements.taskPriorityInput.value = 'Medium';
        elements.taskDueDateInput.value = '';
        elements.taskDescriptionInput.value = '';

        elements.taskModal.classList.remove('hidden');
        elements.taskTitleInput.focus();
    }

    // Open Edit Modal
    function openEditModal(task) {
        state.editingTaskId = task.task_id;
        elements.modalTitle.textContent = 'Edit Task';
        elements.submitBtnText.textContent = 'Update in Cloud Firestore';
        elements.taskIdInput.value = task.task_id;
        elements.taskTitleInput.value = task.title || '';
        elements.taskSubjectInput.value = task.subject || '';
        elements.taskPriorityInput.value = task.priority || 'Medium';
        elements.taskDueDateInput.value = task.due_date || '';
        elements.taskDescriptionInput.value = task.description || '';

        elements.taskModal.classList.remove('hidden');
        elements.taskTitleInput.focus();
    }

    function closeTaskModal() {
        elements.taskModal.classList.add('hidden');
        state.editingTaskId = null;
    }

    // Handle Form Submit (Add or Edit)
    async function handleTaskFormSubmit(e) {
        e.preventDefault();

        const title = elements.taskTitleInput.value.trim();
        if (!title) {
            showToast('Please enter a task title', 'error');
            elements.taskTitleInput.focus();
            return;
        }

        const payload = {
            title: title,
            subject: elements.taskSubjectInput.value.trim() || 'General',
            priority: elements.taskPriorityInput.value,
            due_date: elements.taskDueDateInput.value,
            description: elements.taskDescriptionInput.value.trim()
        };

        elements.submitBtnSpinner.classList.remove('hidden');
        elements.submitTaskBtn.disabled = true;

        try {
            let url = '/api/tasks';
            let method = 'POST';

            if (state.editingTaskId) {
                url = `/api/tasks/${state.editingTaskId}`;
                method = 'PUT';
            }

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showToast(data.message, 'success');
                closeTaskModal();
                fetchTasks();
            } else {
                showToast(data.error || 'Operation failed', 'error');
            }
        } catch (err) {
            showToast('Network error while saving task', 'error');
        } finally {
            elements.submitBtnSpinner.classList.add('hidden');
            elements.submitTaskBtn.disabled = false;
        }
    }

    // Open Delete Modal
    function openDeleteModal(task) {
        state.deletingTaskId = task.task_id;
        elements.deleteTaskTitlePreview.textContent = `"${task.title}"`;
        elements.deleteModal.classList.remove('hidden');
    }

    function closeDeleteModal() {
        elements.deleteModal.classList.add('hidden');
        state.deletingTaskId = null;
    }

    // Confirm Delete Action
    async function confirmDeleteTask() {
        if (!state.deletingTaskId) return;

        elements.deleteSpinner.classList.remove('hidden');
        elements.confirmDeleteBtn.disabled = true;

        try {
            const response = await fetch(`/api/tasks/${state.deletingTaskId}`, {
                method: 'DELETE'
            });
            const data = await response.json();

            if (response.ok && data.success) {
                showToast(data.message, 'success');
                closeDeleteModal();
                fetchTasks();
            } else {
                showToast(data.error || 'Failed to delete task', 'error');
            }
        } catch (err) {
            showToast('Network error while deleting task', 'error');
        } finally {
            elements.deleteSpinner.classList.add('hidden');
            elements.confirmDeleteBtn.disabled = false;
        }
    }

    // Seed Sample Realistic Tasks
    async function handleSeedSamples() {
        elements.seedSamplesBtn.disabled = true;
        showToast('Saving sample tasks directly to Google Cloud Firestore...', 'info');

        try {
            const response = await fetch('/api/seed-samples', { method: 'POST' });
            const data = await response.json();

            if (response.ok && data.success) {
                showToast(data.message, 'success');
                fetchTasks();
            } else {
                showToast(data.error || 'Failed to seed sample tasks to Firestore', 'error');
            }
        } catch (err) {
            showToast('Network error while seeding sample tasks', 'error');
        } finally {
            elements.seedSamplesBtn.disabled = false;
        }
    }

    // -------------------------------------------------------------------------
    // Event Listeners
    // -------------------------------------------------------------------------

    // Search and Filters
    let searchDebounceTimeout = null;
    elements.searchInput.addEventListener('input', (e) => {
        state.filters.search = e.target.value.trim();
        elements.clearSearchBtn.classList.toggle('hidden', !state.filters.search);

        clearTimeout(searchDebounceTimeout);
        searchDebounceTimeout = setTimeout(() => {
            fetchTasks();
        }, 300);
    });

    elements.clearSearchBtn.addEventListener('click', () => {
        elements.searchInput.value = '';
        state.filters.search = '';
        elements.clearSearchBtn.classList.add('hidden');
        fetchTasks();
    });

    elements.statusFilter.addEventListener('change', (e) => {
        state.filters.status = e.target.value;
        fetchTasks();
    });

    elements.priorityFilter.addEventListener('change', (e) => {
        state.filters.priority = e.target.value;
        fetchTasks();
    });

    // Add / Edit Modal triggers
    elements.openAddTaskModalBtn.addEventListener('click', openAddModal);
    elements.emptyStateCreateBtn.addEventListener('click', openAddModal);
    elements.closeModalBtn.addEventListener('click', closeTaskModal);
    elements.cancelModalBtn.addEventListener('click', closeTaskModal);
    elements.taskForm.addEventListener('submit', handleTaskFormSubmit);

    // Delete Modal triggers
    elements.closeDeleteModalBtn.addEventListener('click', closeDeleteModal);
    elements.cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    elements.confirmDeleteBtn.addEventListener('click', confirmDeleteTask);

    // Seed samples trigger
    elements.seedSamplesBtn.addEventListener('click', handleSeedSamples);

    // Diagnostics Modal triggers
    elements.diagnosticsBtn.addEventListener('click', async () => {
        await checkCloudStatus();
        elements.diagnosticsModal.classList.remove('hidden');
    });
    elements.closeDiagModalBtn.addEventListener('click', () => elements.diagnosticsModal.classList.add('hidden'));
    elements.closeDiagBtn.addEventListener('click', () => elements.diagnosticsModal.classList.add('hidden'));

    // Setup Help Modal triggers
    elements.showSetupHelpBtn.addEventListener('click', () => elements.setupHelpModal.classList.remove('hidden'));
    elements.closeSetupHelpBtn.addEventListener('click', () => elements.setupHelpModal.classList.add('hidden'));
    elements.closeSetupBtn.addEventListener('click', () => elements.setupHelpModal.classList.add('hidden'));

    // Retry Firestore Connection
    elements.retryConnectionBtn.addEventListener('click', async () => {
        showToast('Connecting to Cloud Database & Cloudflare Edge (asia-south1)...', 'info');
        const ok = await checkCloudStatus();
        if (ok) {
            showToast('✓ Connected to Real Cloud Database & Edge Network [asia-south1 / Mumbai]', 'success');
            fetchTasks();
        } else {
            showToast('Cloud connection error. Check backend status.', 'error');
        }
    });

    // Dismiss Alert Banner
    if (elements.dismissAlertBtn) {
        elements.dismissAlertBtn.addEventListener('click', () => {
            elements.firestoreAlertBanner.classList.add('hidden');
            showToast('Banner dismissed. You are in Local Testing Mode.', 'info');
        });
    }

    // Close modals on clicking overlay backdrop
    window.addEventListener('click', (e) => {
        if (e.target === elements.taskModal) closeTaskModal();
        if (e.target === elements.deleteModal) closeDeleteModal();
        if (e.target === elements.diagnosticsModal) elements.diagnosticsModal.classList.add('hidden');
        if (e.target === elements.setupHelpModal) elements.setupHelpModal.classList.add('hidden');
    });

    // Keyboard accessibility: ESC key closes modals
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeTaskModal();
            closeDeleteModal();
            elements.diagnosticsModal.classList.add('hidden');
            elements.setupHelpModal.classList.add('hidden');
        }
    });

    // -------------------------------------------------------------------------
    // Initialization
    // -------------------------------------------------------------------------
    (async function init() {
        await checkCloudStatus();
        await fetchTasks();
    })();
});
