/**
 * ChatBiz Standalone Frontend Client Application
 * Communicates with FastAPI backend exclusively via REST JSON endpoints.
 */

// API Configuration
let API_BASE = localStorage.getItem("chatbiz_api_base") || "http://127.0.0.1:8000";

// Global State
let currentTab = "analytics";
let allClients = [];
let allInvoices = [];
let currentInvoiceFilter = "all";
let isBackendOnline = false;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("config-api-url").value = API_BASE;
  document.getElementById("offline-url-text").textContent = API_BASE;
  
  // Update export button link
  const exportBtn = document.getElementById("btn-export-csv");
  if (exportBtn) exportBtn.href = `${API_BASE}/api/export/invoices`;

  // Set default dates in form modals
  const todayStr = new Date().toISOString().split("T")[0];
  const dueInput = document.getElementById("invoice-due");
  if (dueInput) dueInput.value = todayStr;
  const paymentDateInput = document.getElementById("payment-date");
  if (paymentDateInput) paymentDateInput.value = todayStr;

  // Check connection and load initial view
  checkBackendHealth().then(online => {
    if (online) {
      loadAllData();
      const hash = (window.location.hash || "").replace("#", "");
      if (["analytics", "clients", "invoices", "payments", "reminders"].includes(hash)) {
        switchTab(hash);
      }
    }
  });

  window.addEventListener("hashchange", () => {
    const hash = (window.location.hash || "").replace("#", "");
    if (["analytics", "clients", "invoices", "payments", "reminders"].includes(hash)) {
      switchTab(hash);
    }
  });

  // Periodic health check every 10 seconds
  setInterval(() => checkBackendHealth(false), 10000);

});

/* ==========================================================================
   Backend Connectivity
   ========================================================================== */
async function checkBackendHealth(showToastOnError = false) {
  const badge = document.getElementById("api-status-badge");
  const label = document.getElementById("api-status-label");
  const offlineBanner = document.getElementById("offline-banner");

  try {
    const res = await fetch(`${API_BASE}/`, { method: "GET" });
    if (res.ok) {
      const data = await res.json();
      badge.className = "status-indicator-pill online";
      label.textContent = "API Online (8000)";
      offlineBanner.style.display = "none";
      isBackendOnline = true;
      return true;
    }
    throw new Error(`HTTP ${res.status}`);
  } catch (err) {
    badge.className = "status-indicator-pill offline";
    label.textContent = "API Offline";
    offlineBanner.style.display = "flex";
    isBackendOnline = false;
    if (showToastOnError) {
      showToast("Cannot connect to backend API server at " + API_BASE, "error");
    }
    return false;
  }
}

function openApiConfigModal() {
  document.getElementById("config-api-url").value = API_BASE;
  openModal("modal-api-config");
}

function saveApiConfig() {
  const input = document.getElementById("config-api-url");
  let newUrl = input.value.trim().replace(/\/+$/, "");
  if (!newUrl) newUrl = "http://127.0.0.1:8000";
  API_BASE = newUrl;
  localStorage.setItem("chatbiz_api_base", API_BASE);
  document.getElementById("offline-url-text").textContent = API_BASE;

  const exportBtn = document.getElementById("btn-export-csv");
  if (exportBtn) exportBtn.href = `${API_BASE}/api/export/invoices`;

  closeModal("modal-api-config");
  showToast("API Base URL updated. Reconnecting...", "info");
  checkBackendHealth(true).then(online => {
    if (online) loadAllData();
  });
}

/* ==========================================================================
   Navigation & Tabs
   ========================================================================== */
function switchTab(tabName) {
  currentTab = tabName;
  if (window.location.hash !== `#${tabName}`) {
    history.replaceState(null, null, `#${tabName}`);
  }

  // Update nav buttons
  document.querySelectorAll(".nav-tab").forEach(btn => btn.classList.remove("active"));
  const activeBtn = document.getElementById(`tab-btn-${tabName}`);
  if (activeBtn) activeBtn.classList.add("active");

  // Update panes
  document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));
  const activePane = document.getElementById(`pane-${tabName}`);
  if (activePane) activePane.classList.add("active");

  refreshCurrentTab(false);
}


function refreshCurrentTab(userInitiated = false) {
  if (userInitiated) {
    const refreshBtn = document.getElementById("btn-refresh");
    if (refreshBtn) refreshBtn.classList.add("spinning");
  }

  const promise = (() => {
    switch (currentTab) {
      case "analytics": return loadAnalytics();
      case "clients": return loadClients();
      case "invoices": return loadInvoices();
      case "payments": return loadPayments();
      case "reminders": return loadRemindersAndVoice();
      default: return loadAnalytics();
    }
  })();

  promise.finally(() => {
    if (userInitiated) {
      setTimeout(() => {
        const refreshBtn = document.getElementById("btn-refresh");
        if (refreshBtn) refreshBtn.classList.remove("spinning");
        showToast("Data refreshed successfully", "success");
      }, 350);
    }
  });
}

function loadAllData() {
  loadAnalytics();
  loadClients();
  loadInvoices();
  loadPayments();
  loadRemindersAndVoice();
}

/* ==========================================================================
   Tab 1: Analytics
   ========================================================================== */
async function loadAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/api/analytics`);
    if (!res.ok) throw new Error("Analytics fetch failed");
    const data = await res.json();
    const ov = data.overall || {};

    // Update KPI Card values
    document.getElementById("kpi-total-invoiced").textContent = formatCurrency(ov.total_invoiced);
    document.getElementById("kpi-invoice-count").textContent = ov.invoice_count || 0;
    document.getElementById("kpi-paid-amount").textContent = formatCurrency(ov.paid_amount);
    document.getElementById("kpi-paid-count").textContent = `${ov.paid_count || 0} Paid`;
    document.getElementById("kpi-pending-amount").textContent = formatCurrency(ov.pending_amount);
    document.getElementById("kpi-pending-count").textContent = `${ov.pending_count || 0} Pending`;
    document.getElementById("kpi-overdue-amount").textContent = formatCurrency(ov.overdue_amount);
    document.getElementById("kpi-overdue-count").textContent = `${ov.overdue_count || 0} Overdue`;
    document.getElementById("kpi-client-count").textContent = ov.client_count || 0;

    const rate = ov.collection_rate_pct || 0;
    document.getElementById("kpi-collection-rate").textContent = `${rate}%`;
    document.getElementById("kpi-collection-progress").style.width = `${Math.min(rate, 100)}%`;

    // Timestamp
    document.getElementById("analytics-updated-at").textContent = `Synced: ${new Date().toLocaleTimeString()}`;

    // Populate Client Leaderboard Table
    const clients = data.clients || [];
    const tbody = document.getElementById("analytics-clients-tbody");
    if (clients.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No client analytics found.</td></tr>`;
      return;
    }

    tbody.innerHTML = clients.map(c => {
      const collRate = c.total_invoiced > 0 ? Math.round((c.paid / c.total_invoiced) * 100) : 0;
      return `
        <tr>
          <td>
            <strong>${escapeHtml(c.name)}</strong>
            <div class="text-muted text-sm">${escapeHtml(c.phone || "")}</div>
          </td>
          <td><span class="badge badge-neutral">${c.invoices}</span></td>
          <td><strong>${formatCurrency(c.total_invoiced)}</strong></td>
          <td class="value-success">${formatCurrency(c.paid)}</td>
          <td class="value-warning">${formatCurrency(c.pending)}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <div style="flex:1;height:5px;background:rgba(255,255,255,0.1);border-radius:4px;overflow:hidden;">
                <div style="width:${Math.min(collRate, 100)}%;height:100%;background:${collRate >= 70 ? '#10b981' : collRate >= 40 ? '#f59e0b' : '#ef4444'};"></div>
              </div>
              <span class="text-sm font-mono">${collRate}%</span>
            </div>
          </td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.error("loadAnalytics error:", err);
  }
}

/* ==========================================================================
   Tab 2: Clients
   ========================================================================== */
async function loadClients() {
  try {
    const res = await fetch(`${API_BASE}/api/clients`);
    if (!res.ok) throw new Error("Clients fetch failed");
    allClients = await res.json();

    // Update count badges
    document.getElementById("badge-clients-count").textContent = allClients.length;

    // Populate client selector dropdowns in invoice modals
    const clientSelect = document.getElementById("invoice-client-id");
    if (clientSelect) {
      clientSelect.innerHTML = `<option value="">-- Choose Client --</option>` +
        allClients.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("");
    }

    renderClients(allClients);
  } catch (err) {
    console.error("loadClients error:", err);
  }
}

function renderClients(clients) {
  const tbody = document.getElementById("clients-tbody");
  if (!clients || clients.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No clients registered.</td></tr>`;
    return;
  }

  tbody.innerHTML = clients.map(c => `
    <tr>
      <td class="mono-cell">#C-${String(c.id).padStart(3, "0")}</td>
      <td>
        <strong>${escapeHtml(c.name)}</strong>
      </td>
      <td>
        <a href="tel:${escapeHtml(c.phone)}" class="text-sm" style="color:#38bdf8;text-decoration:none;">${escapeHtml(c.phone || "—")}</a>
      </td>
      <td class="text-sm text-muted">${escapeHtml(c.email || "—")}</td>
      <td><span class="badge badge-neutral">${c.invoices_count || 0}</span></td>
      <td><strong>${formatCurrency(c.total_invoiced || 0)}</strong></td>
      <td class="value-success">${formatCurrency(c.paid_amount || 0)}</td>
      <td class="${c.pending_amount > 0 ? 'value-warning' : 'text-muted'}">${formatCurrency(c.pending_amount || 0)}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="filterInvoicesByClient('${escapeHtml(c.name)}')">
          View Invoices
        </button>
      </td>
    </tr>
  `).join("");
}

function filterClients() {
  const q = (document.getElementById("client-search-input").value || "").toLowerCase();
  const filtered = allClients.filter(c => 
    c.name.toLowerCase().includes(q) ||
    (c.phone && c.phone.toLowerCase().includes(q)) ||
    (c.email && c.email.toLowerCase().includes(q))
  );
  renderClients(filtered);
}

function filterInvoicesByClient(clientName) {
  switchTab("invoices");
  const searchInput = document.getElementById("invoice-search-input");
  if (searchInput) {
    searchInput.value = clientName;
    handleInvoiceSearch();
  }
}

/* ==========================================================================
   Tab 3: Invoices
   ========================================================================== */
async function loadInvoices() {
  try {
    let url = `${API_BASE}/api/invoices`;
    if (currentInvoiceFilter && currentInvoiceFilter !== "all") {
      url += `?status=${encodeURIComponent(currentInvoiceFilter)}`;
    }

    const res = await fetch(url);
    if (!res.ok) throw new Error("Invoices fetch failed");
    allInvoices = await res.json();

    document.getElementById("badge-invoices-count").textContent = allInvoices.length;

    // Populate payment invoice select modal
    const pmtInvoiceSelect = document.getElementById("payment-invoice-id");
    if (pmtInvoiceSelect) {
      pmtInvoiceSelect.innerHTML = `<option value="">-- Choose Invoice --</option>` +
        allInvoices.map(i => `<option value="${i.id}" data-amount="${i.amount}">#INV-${String(i.id).padStart(4, "0")} — ${escapeHtml(i.client_name)} (${formatCurrency(i.amount)}) [${i.status}]</option>`).join("");
    }

    renderInvoices(allInvoices);
  } catch (err) {
    console.error("loadInvoices error:", err);
  }
}

function setInvoiceFilter(statusFilter, btnElement) {
  currentInvoiceFilter = statusFilter;
  document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
  if (btnElement) btnElement.classList.add("active");
  loadInvoices();
}

function handleInvoiceSearch() {
  const q = (document.getElementById("invoice-search-input").value || "").toLowerCase();
  const filtered = allInvoices.filter(i => 
    i.description.toLowerCase().includes(q) ||
    i.client_name.toLowerCase().includes(q) ||
    String(i.id).includes(q)
  );
  renderInvoices(filtered);
}

function renderInvoices(invoices) {
  const tbody = document.getElementById("invoices-tbody");
  if (!invoices || invoices.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No invoices match criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = invoices.map(i => {
    const statusClass = i.status === "Paid" ? "badge-success" : i.status === "Overdue" ? "badge-danger" : "badge-warning";
    return `
      <tr>
        <td class="mono-cell">#INV-${String(i.id).padStart(4, "0")}</td>
        <td>
          <strong>${escapeHtml(i.client_name)}</strong>
          <div class="text-muted text-sm">${escapeHtml(i.client_phone || "")}</div>
        </td>
        <td>${escapeHtml(i.description)}</td>
        <td><strong>${formatCurrency(i.amount)}</strong></td>
        <td><span class="font-mono text-sm">${i.due_date || "—"}</span></td>
        <td><span class="badge ${statusClass}">${i.status}</span></td>
        <td class="font-mono text-sm text-muted">${escapeHtml(i.upi_id || "—")}</td>
        <td>
          ${i.recurring ? `<span class="badge badge-purple">${i.recurrence || "Recurring"}</span>` : `<span class="text-muted text-sm">One-Time</span>`}
        </td>
        <td>
          <div style="display:flex;gap:6px;">
            ${i.status !== "Paid" ? `
              <button class="btn btn-accent btn-sm" onclick="markInvoicePaid(${i.id})">
                Mark Paid
              </button>
            ` : `
              <span class="text-muted text-sm">Settled</span>
            `}
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

async function markInvoicePaid(invoiceId) {
  try {
    const res = await fetch(`${API_BASE}/api/invoices/${invoiceId}/mark-paid`, { method: "POST" });
    if (!res.ok) throw new Error("Could not update invoice");
    const data = await res.json();
    showToast(data.message || "Invoice marked as Paid!", "success");
    loadAllData();
  } catch (err) {
    showToast("Error updating invoice: " + err.message, "error");
  }
}

/* ==========================================================================
   Tab 4: Payments Ledger
   ========================================================================== */
async function loadPayments() {
  try {
    const res = await fetch(`${API_BASE}/api/payments`);
    if (!res.ok) throw new Error("Payments fetch failed");
    const payments = await res.json();

    const tbody = document.getElementById("payments-tbody");
    if (payments.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No payment records found.</td></tr>`;
      return;
    }

    tbody.innerHTML = payments.map(p => {
      const sourceBadge = p.source === "ocr" 
        ? `<span class="badge badge-purple">OCR Scan</span>` 
        : p.source === "upi_webhook" 
        ? `<span class="badge badge-success">UPI Instant</span>` 
        : `<span class="badge badge-neutral">Manual Receipt</span>`;

      return `
        <tr>
          <td class="mono-cell">#PMT-${String(p.id).padStart(4, "0")}</td>
          <td class="font-mono text-sm">${escapeHtml(p.transaction_id || "—")}</td>
          <td>
            <strong>${escapeHtml(p.client_name || "—")}</strong>
            <div class="text-muted text-sm">#INV-${String(p.invoice_id).padStart(4, "0")}: ${escapeHtml(p.invoice_description || "")}</div>
          </td>
          <td class="value-success"><strong>${formatCurrency(p.amount)}</strong></td>
          <td class="font-mono text-sm">${p.payment_date || "—"}</td>
          <td>${sourceBadge}</td>
          <td class="text-sm text-muted">${escapeHtml(p.raw_text || "—")}</td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("loadPayments error:", err);
  }
}

function populatePaymentAmount(invId) {
  const select = document.getElementById("payment-invoice-id");
  const selectedOpt = select.options[select.selectedIndex];
  if (selectedOpt && selectedOpt.dataset.amount) {
    document.getElementById("payment-amount").value = selectedOpt.dataset.amount;
  }
}

/* ==========================================================================
   Tab 5: Reminders & Voice Commands
   ========================================================================== */
async function loadRemindersAndVoice() {
  // 1. Reminders
  try {
    const res = await fetch(`${API_BASE}/api/reminders`);
    if (res.ok) {
      const reminders = await res.json();
      const container = document.getElementById("reminders-list-container");
      if (reminders.length === 0) {
        container.innerHTML = `<div class="text-center py-4 text-muted">No scheduled payment reminders.</div>`;
      } else {
        container.innerHTML = reminders.map(r => {
          const typeBadge = r.reminder_type === "OVERDUE" 
            ? `<span class="badge badge-danger">OVERDUE ALERT</span>`
            : r.reminder_type === "DUE_TODAY" 
            ? `<span class="badge badge-warning">DUE TODAY</span>`
            : `<span class="badge badge-neutral">UPCOMING</span>`;

          const isSent = r.status === "SENT";

          return `
            <div class="reminder-item">
              <div class="reminder-left">
                <div style="display:flex;align-items:center;gap:8px;">
                  ${typeBadge}
                  <span class="reminder-title">${escapeHtml(r.client_name)}</span>
                  <span class="text-muted text-sm">(${escapeHtml(r.client_phone)})</span>
                </div>
                <div class="text-sm" style="color:#cbd5e1;">${escapeHtml(r.invoice_description)} — <strong>${formatCurrency(r.invoice_amount)}</strong></div>
                <div class="reminder-meta">
                  <span>Scheduled: ${r.scheduled_for}</span>
                  ${isSent ? `<span class="value-success">Sent: ${r.sent_at}</span>` : `<span class="value-warning">Status: PENDING</span>`}
                </div>
              </div>
              <div>
                ${!isSent ? `
                  <button class="btn btn-accent btn-sm" onclick="triggerSendReminder(${r.id})">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                    Send WhatsApp
                  </button>
                ` : `
                  <span class="badge badge-success">Delivered</span>
                `}
              </div>
            </div>
          `;
        }).join("");
      }
    }
  } catch (err) {
    console.error("loadReminders error:", err);
  }

  // 2. Voice Commands
  try {
    const res = await fetch(`${API_BASE}/api/voice-commands`);
    if (res.ok) {
      const logs = await res.json();
      const feed = document.getElementById("voice-feed-container");
      if (logs.length === 0) {
        feed.innerHTML = `<div class="text-center py-4 text-muted">No voice commands recorded.</div>`;
      } else {
        feed.innerHTML = logs.map(vc => `
          <div class="voice-item">
            <div class="voice-transcript">"${escapeHtml(vc.transcript)}"</div>
            <div class="voice-meta">
              <span class="badge badge-purple">${escapeHtml(vc.intent)}</span>
              <span>${vc.created_at || "Just now"}</span>
            </div>
          </div>
        `).join("");
      }
    }
  } catch (err) {
    console.error("loadVoiceCommands error:", err);
  }
}

async function triggerSendReminder(reminderId) {
  try {
    const res = await fetch(`${API_BASE}/api/reminders/${reminderId}/send`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to send reminder");
    const data = await res.json();
    showToast(data.message || "WhatsApp reminder simulated successfully!", "success");
    loadRemindersAndVoice();
  } catch (err) {
    showToast("Error sending reminder: " + err.message, "error");
  }
}

// Web Speech API Voice Recognition
let recognition = null;
let isRecording = false;

function toggleVoiceRecording() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showToast("Speech recognition is not supported in this browser. Please use Chrome or Edge.", "error");
    return;
  }

  const micBtn = document.getElementById("btn-mic");
  const input = document.getElementById("voice-transcript-input");

  if (isRecording) {
    if (recognition) recognition.stop();
    isRecording = false;
    if (micBtn) {
      micBtn.innerHTML = "🎙️ Speak";
      micBtn.classList.remove("recording");
    }
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-IN"; // English (India)
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isRecording = true;
    if (micBtn) {
      micBtn.innerHTML = "🔴 Listening...";
      micBtn.classList.add("recording");
    }
    showToast("Listening... Speak your command into the microphone!", "info");
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    input.value = transcript;
    showToast(`Recognized: "${transcript}"`, "info");
    submitVoiceCommand();
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    showToast(`Microphone notice: ${event.error}`, "error");
    isRecording = false;
    if (micBtn) {
      micBtn.innerHTML = "🎙️ Speak";
      micBtn.classList.remove("recording");
    }
  };

  recognition.onend = () => {
    isRecording = false;
    if (micBtn) {
      micBtn.innerHTML = "🎙️ Speak";
      micBtn.classList.remove("recording");
    }
  };

  try {
    recognition.start();
  } catch (err) {
    console.error("Recognition start error:", err);
  }
}

async function submitVoiceCommand() {
  const input = document.getElementById("voice-transcript-input");
  const text = input.value.trim();
  if (!text) return;

  // Simple client-side intent classifier demo
  let inferredIntent = "GENERAL_QUERY";
  const lower = text.toLowerCase();
  if (lower.includes("invoice") || lower.includes("create") || lower.includes("generate") || lower.includes("bill")) inferredIntent = "CREATE_INVOICE";
  else if (lower.includes("reminder") || lower.includes("remind")) inferredIntent = "SEND_REMINDER";
  else if (lower.includes("payment") || lower.includes("paid")) inferredIntent = "RECORD_PAYMENT";
  else if (lower.includes("overdue")) inferredIntent = "VIEW_OVERDUE";
  else if (lower.includes("revenue") || lower.includes("analytics") || lower.includes("summary")) inferredIntent = "VIEW_ANALYTICS";
  else if (lower.includes("client")) inferredIntent = "LIST_CLIENTS";

  try {
    const res = await fetch(`${API_BASE}/api/voice-commands`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript: text, intent: inferredIntent })
    });
    if (!res.ok) throw new Error("Could not log voice command");
    const data = await res.json();
    input.value = "";
    
    if (data.action_taken) {
      showToast(`⚡ ${data.action_taken}`, "success");
    } else {
      showToast(`Voice command processed: [${inferredIntent}]`, "info");
    }
    loadAllData();
  } catch (err) {
    showToast("Error processing voice command: " + err.message, "error");
  }
}



/* ==========================================================================
   Action Modals & Form Handlers
   ========================================================================== */
function openNewClientModal() { openModal("modal-client"); }
function openNewInvoiceModal() { openModal("modal-invoice"); }
function openNewPaymentModal() { openModal("modal-payment"); }

function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.style.display = "flex";
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.style.display = "none";
}

async function handleCreateClient(e) {
  e.preventDefault();
  const name = document.getElementById("client-name").value.trim();
  const phone = document.getElementById("client-phone").value.trim();
  const email = document.getElementById("client-email").value.trim();

  try {
    const res = await fetch(`${API_BASE}/api/clients`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, phone, email: email || null })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create client");
    }
    const data = await res.json();
    closeModal("modal-client");
    document.getElementById("form-create-client").reset();
    showToast(`Client "${data.client.name}" registered successfully!`, "success");
    loadAllData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleCreateInvoice(e) {
  e.preventDefault();
  const clientId = parseInt(document.getElementById("invoice-client-id").value, 10);
  const desc = document.getElementById("invoice-desc").value.trim();
  const amount = parseFloat(document.getElementById("invoice-amount").value);
  const due = document.getElementById("invoice-due").value;
  const upi = document.getElementById("invoice-upi").value.trim();
  const recurring = parseInt(document.getElementById("invoice-recurring").value, 10);
  const recurrence = document.getElementById("invoice-recurrence").value || null;

  try {
    const res = await fetch(`${API_BASE}/api/invoices`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: clientId,
        description: desc,
        amount: amount,
        due_date: due,
        upi_id: upi || null,
        recurring: recurring,
        recurrence: recurrence
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create invoice");
    }
    const data = await res.json();
    closeModal("modal-invoice");
    document.getElementById("form-create-invoice").reset();
    showToast(`Invoice #INV-${String(data.invoice.id).padStart(4, "0")} generated!`, "success");
    loadAllData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleCreatePayment(e) {
  e.preventDefault();
  const invoiceId = parseInt(document.getElementById("payment-invoice-id").value, 10);
  const amount = parseFloat(document.getElementById("payment-amount").value);
  const pDate = document.getElementById("payment-date").value;
  const source = document.getElementById("payment-source").value;
  const txId = document.getElementById("payment-txid").value.trim();
  const rawText = document.getElementById("payment-raw").value.trim();

  try {
    const res = await fetch(`${API_BASE}/api/payments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        invoice_id: invoiceId,
        amount: amount,
        payment_date: pDate,
        source: source,
        transaction_id: txId || null,
        raw_text: rawText || null
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to record payment");
    }
    closeModal("modal-payment");
    document.getElementById("form-create-payment").reset();
    showToast("Payment recorded and verified successfully!", "success");
    loadAllData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function triggerDbSeed(force = true) {
  if (force && !confirm("Re-seed sample database? This will refresh clients, invoices, payments, reminders, and voice commands.")) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/db/seed?force=${force}`, { method: "POST" });
    if (!res.ok) throw new Error("Seeding failed");
    const data = await res.json();
    showToast(`Sample data refreshed: ${data.clients_added || 8} clients, ${data.invoices_added || 16} invoices loaded.`, "success");
    loadAllData();
  } catch (err) {
    showToast("Failed to seed database: " + err.message, "error");
  }
}

/* ==========================================================================
   Utilities & Helpers
   ========================================================================== */
function formatCurrency(num) {
  const val = parseFloat(num) || 0;
  return "₹ " + val.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const iconSvg = type === "success" 
    ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`
    : type === "error"
    ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`
    : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;

  toast.innerHTML = `${iconSvg}<span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
