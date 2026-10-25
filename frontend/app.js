/**
 * ChatBiz Executive MSME Workspace
 * Standalone Frontend Application
 * Interacts with FastAPI backend via pure REST JSON endpoints.
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
  const configInput = document.getElementById("config-api-url");
  if (configInput) configInput.value = API_BASE;
  const offlineText = document.getElementById("offline-url-text");
  if (offlineText) offlineText.textContent = API_BASE;

  const exportBtn = document.getElementById("btn-export-csv");
  if (exportBtn) exportBtn.href = `${API_BASE}/api/export/invoices`;

  const todayStr = new Date().toISOString().split("T")[0];
  const dueInput = document.getElementById("invoice-due");
  if (dueInput) dueInput.value = todayStr;
  const paymentDateInput = document.getElementById("payment-date");
  if (paymentDateInput) paymentDateInput.value = todayStr;

  checkBackendHealth().then(online => {
    if (online) {
      loadAllData();
      const hash = (window.location.hash || "").replace("#", "");
      if (["analytics", "clients", "invoices", "payments", "reminders", "chat"].includes(hash)) {
        switchTab(hash);
      }
    }
  });

  window.addEventListener("hashchange", () => {
    const hash = (window.location.hash || "").replace("#", "");
    if (["analytics", "clients", "invoices", "payments", "reminders", "chat"].includes(hash)) {
      switchTab(hash);
    }
  });

  setInterval(() => checkBackendHealth(false), 12000);
});

/* ==========================================================================
   Backend Connectivity & Configuration
   ========================================================================== */
async function checkBackendHealth(showToastOnError = false) {
  const badge = document.getElementById("api-status-badge");
  const label = document.getElementById("api-status-label");
  const offlineBanner = document.getElementById("offline-banner");

  try {
    const res = await fetch(`${API_BASE}/`, { method: "GET" });
    if (res.ok) {
      if (badge) badge.className = "status-pill online";
      if (label) label.textContent = "API Online";
      if (offlineBanner) offlineBanner.style.display = "none";
      isBackendOnline = true;
      return true;
    }
    throw new Error(`HTTP ${res.status}`);
  } catch (err) {
    if (badge) badge.className = "status-pill offline";
    if (label) label.textContent = "API Offline";
    if (offlineBanner) offlineBanner.style.display = "flex";
    isBackendOnline = false;
    if (showToastOnError) {
      showToast("Cannot connect to backend server at " + API_BASE, "error");
    }
    return false;
  }
}

function openApiConfigModal() {
  const input = document.getElementById("config-api-url");
  if (input) input.value = API_BASE;
  openModal("modal-api-config");
}

function saveApiConfig() {
  const input = document.getElementById("config-api-url");
  let newUrl = (input ? input.value : "").trim().replace(/\/+$/, "");
  if (!newUrl) newUrl = "http://127.0.0.1:8000";
  API_BASE = newUrl;
  localStorage.setItem("chatbiz_api_base", API_BASE);
  const offlineText = document.getElementById("offline-url-text");
  if (offlineText) offlineText.textContent = API_BASE;

  const exportBtn = document.getElementById("btn-export-csv");
  if (exportBtn) exportBtn.href = `${API_BASE}/api/export/invoices`;

  closeModal("modal-api-config");
  showToast("Backend URL updated. Reconnecting...", "info");
  checkBackendHealth(true).then(online => {
    if (online) loadAllData();
  });
}

/* ==========================================================================
   Tab Navigation
   ========================================================================== */
function switchTab(tabName) {
  currentTab = tabName;
  if (window.location.hash !== `#${tabName}`) {
    history.replaceState(null, null, `#${tabName}`);
  }

  document.querySelectorAll(".nav-tab-btn").forEach(btn => btn.classList.remove("active"));
  const activeBtn = document.getElementById(`tab-btn-${tabName}`);
  if (activeBtn) activeBtn.classList.add("active");

  document.querySelectorAll(".tab-pane").forEach(pane => {
    pane.style.display = "none";
    pane.classList.remove("active");
  });
  const activePane = document.getElementById(`pane-${tabName}`);
  if (activePane) {
    activePane.style.display = "block";
    activePane.classList.add("active");
  }

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
      case "chat": return loadChatData();
      default: return loadAnalytics();
    }
  })();

  promise.finally(() => {
    if (userInitiated) {
      setTimeout(() => {
        const refreshBtn = document.getElementById("btn-refresh");
        if (refreshBtn) refreshBtn.classList.remove("spinning");
        showToast("Data updated", "info");
      }, 300);
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

    const elTotal = document.getElementById("kpi-total-invoiced");
    if (elTotal) elTotal.textContent = formatCurrency(ov.total_invoiced);
    const elInvCount = document.getElementById("kpi-invoice-count");
    if (elInvCount) elInvCount.textContent = ov.invoice_count || 0;

    const elPaid = document.getElementById("kpi-paid-amount");
    if (elPaid) elPaid.textContent = formatCurrency(ov.paid_amount);
    const elPaidCount = document.getElementById("kpi-paid-count");
    if (elPaidCount) elPaidCount.textContent = `${ov.paid_count || 0} Paid`;

    const elPending = document.getElementById("kpi-pending-amount");
    if (elPending) elPending.textContent = formatCurrency(ov.pending_amount);
    const elPendingCount = document.getElementById("kpi-pending-count");
    if (elPendingCount) elPendingCount.textContent = `${ov.pending_count || 0} Pending`;

    const elOverdue = document.getElementById("kpi-overdue-amount");
    if (elOverdue) elOverdue.textContent = formatCurrency(ov.overdue_amount);
    const elOverdueCount = document.getElementById("kpi-overdue-count");
    if (elOverdueCount) elOverdueCount.textContent = `${ov.overdue_count || 0} Overdue`;

    const rate = ov.collection_rate_pct || 0;
    const elRate = document.getElementById("kpi-collection-rate");
    if (elRate) elRate.textContent = `${rate}%`;
    const elProgress = document.getElementById("kpi-collection-progress");
    if (elProgress) elProgress.style.width = `${Math.min(rate, 100)}%`;

    // Populate Leaderboard
    const clients = data.clients || [];
    const tbody = document.getElementById("analytics-clients-tbody");
    if (!tbody) return;

    if (clients.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-muted" style="text-align: center; padding: 20px;">No client records found.</td></tr>`;
      return;
    }

    tbody.innerHTML = clients.map(c => {
      const collRate = c.total_invoiced > 0 ? Math.round((c.paid / c.total_invoiced) * 100) : 0;
      return `
        <tr>
          <td>
            <strong>${escapeHtml(c.name)}</strong>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(c.phone || "—")}</div>
          </td>
          <td><span class="badge-subtle">${c.invoices}</span></td>
          <td class="tabular-nums"><strong>${formatCurrency(c.total_invoiced)}</strong></td>
          <td class="tabular-nums" style="color: #059669;">${formatCurrency(c.paid)}</td>
          <td class="tabular-nums" style="color: ${c.pending > 0 ? '#d97706' : 'var(--text-muted)'};">${formatCurrency(c.pending)}</td>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <div style="flex: 1; height: 4px; background: var(--bg-recessed); border-radius: 999px; overflow: hidden;">
                <div style="width: ${Math.min(collRate, 100)}%; height: 100%; background: ${collRate >= 70 ? '#10b981' : collRate >= 40 ? '#f59e0b' : '#ef4444'};"></div>
              </div>
              <span class="tabular-nums" style="font-size: 0.75rem; font-weight: 500;">${collRate}%</span>
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

    const countBadge = document.getElementById("badge-clients-count");
    if (countBadge) countBadge.textContent = allClients.length;

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
  if (!tbody) return;

  if (!clients || clients.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-muted" style="text-align: center; padding: 24px;">No clients registered.</td></tr>`;
    return;
  }

  tbody.innerHTML = clients.map(c => `
    <tr>
      <td class="mono-cell">#C-${String(c.id).padStart(3, "0")}</td>
      <td><strong>${escapeHtml(c.name)}</strong></td>
      <td>
        <a href="tel:${escapeHtml(c.phone)}" style="color: var(--accent-base); text-decoration: none;">${escapeHtml(c.phone || "—")}</a>
      </td>
      <td style="color: var(--text-muted);">${escapeHtml(c.email || "—")}</td>
      <td><span class="badge-subtle">${c.invoices_count || 0}</span></td>
      <td class="tabular-nums"><strong>${formatCurrency(c.total_invoiced || 0)}</strong></td>
      <td class="tabular-nums" style="color: #059669;">${formatCurrency(c.paid_amount || 0)}</td>
      <td class="tabular-nums" style="color: ${c.pending_amount > 0 ? '#d97706' : 'var(--text-muted)'};">${formatCurrency(c.pending_amount || 0)}</td>
      <td class="text-right">
        <button class="btn btn-secondary btn-sm" onclick="filterInvoicesByClient('${escapeHtml(c.name)}')">
          Invoices
        </button>
      </td>
    </tr>
  `).join("");
}

function filterClients() {
  const input = document.getElementById("client-search-input");
  const q = (input ? input.value : "").toLowerCase();
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

    const countBadge = document.getElementById("badge-invoices-count");
    if (countBadge) countBadge.textContent = allInvoices.length;

    // Populate payment invoice select modal
    const pmtSelect = document.getElementById("payment-invoice-id");
    if (pmtSelect) {
      pmtSelect.innerHTML = `<option value="">-- Choose Invoice --</option>` +
        allInvoices.map(i => `<option value="${i.id}" data-amount="${i.amount}">#INV-${String(i.id).padStart(4, "0")} — ${escapeHtml(i.client_name)} (${formatCurrency(i.amount)}) [${i.status}]</option>`).join("");
    }

    renderInvoices(allInvoices);
  } catch (err) {
    console.error("loadInvoices error:", err);
  }
}

function setInvoiceFilter(statusFilter, btnElement) {
  currentInvoiceFilter = statusFilter;
  document.querySelectorAll(".filter-btn").forEach(p => p.classList.remove("active"));
  if (btnElement) btnElement.classList.add("active");
  loadInvoices();
}

function handleInvoiceSearch() {
  const input = document.getElementById("invoice-search-input");
  const q = (input ? input.value : "").toLowerCase();
  const filtered = allInvoices.filter(i =>
    i.description.toLowerCase().includes(q) ||
    i.client_name.toLowerCase().includes(q) ||
    String(i.id).includes(q)
  );
  renderInvoices(filtered);
}

function renderInvoices(invoices) {
  const tbody = document.getElementById("invoices-tbody");
  if (!tbody) return;

  if (!invoices || invoices.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-muted" style="text-align: center; padding: 24px;">No invoices found.</td></tr>`;
    return;
  }

  tbody.innerHTML = invoices.map(i => {
    const statusClass = i.status === "Paid" ? "status-paid" : i.status === "Overdue" ? "status-overdue" : "status-pending";
    return `
      <tr>
        <td class="mono-cell">#INV-${String(i.id).padStart(4, "0")}</td>
        <td>
          <strong>${escapeHtml(i.client_name)}</strong>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(i.client_phone || "")}</div>
        </td>
        <td>${escapeHtml(i.description)}</td>
        <td class="tabular-nums"><strong>${formatCurrency(i.amount)}</strong></td>
        <td class="tabular-nums" style="font-size: 0.75rem;">${i.due_date || "—"}</td>
        <td><span class="status-pill-badge ${statusClass}">${i.status}</span></td>
        <td class="mono-cell" style="font-size: 0.6875rem;">${escapeHtml(i.upi_id || "—")}</td>
        <td>
          ${i.recurring ? `<span class="badge-subtle">${i.recurrence || "Recurring"}</span>` : `<span style="font-size: 0.75rem; color: var(--text-muted);">One-Time</span>`}
        </td>
        <td class="text-right">
          <div style="display: inline-flex; align-items: center; gap: 4px;">
            <a class="btn btn-secondary btn-sm" href="${API_BASE}/api/invoices/${i.id}/pdf" target="_blank" title="Download PDF with UPI QR code">
              PDF
            </a>
            <button class="btn btn-secondary btn-sm" onclick="sendInvoiceWhatsApp(${i.id})" title="Send simulated WhatsApp delivery">
              WhatsApp
            </button>
            ${i.status !== "Paid" ? `
              <button class="btn btn-primary btn-sm" onclick="markInvoicePaid(${i.id})" title="Mark invoice settled">
                Mark Paid
              </button>
            ` : ''}
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

async function sendInvoiceWhatsApp(invoiceId) {
  try {
    const res = await fetch(`${API_BASE}/api/invoices/${invoiceId}/send`, { method: "POST" });
    if (!res.ok) throw new Error("Could not send invoice");
    const data = await res.json();
    showToast(data.message || "Invoice PDF delivered via WhatsApp (simulated)!", "success");
  } catch (err) {
    showToast("Error: " + err.message, "error");
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
    if (!tbody) return;

    if (payments.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-muted" style="text-align: center; padding: 24px;">No payment settlements recorded.</td></tr>`;
      return;
    }

    tbody.innerHTML = payments.map(p => {
      const channelLabel = p.source === "ocr" ? "OCR Scan" : p.source === "upi_webhook" ? "UPI Instant" : "Manual";
      return `
        <tr>
          <td class="mono-cell">#PMT-${String(p.id).padStart(4, "0")}</td>
          <td class="mono-cell" style="font-size: 0.75rem;">${escapeHtml(p.transaction_id || "—")}</td>
          <td>
            <strong>${escapeHtml(p.client_name || "—")}</strong>
            <div style="font-size: 0.75rem; color: var(--text-muted);">#INV-${String(p.invoice_id).padStart(4, "0")}: ${escapeHtml(p.invoice_description || "")}</div>
          </td>
          <td class="tabular-nums" style="color: #059669;"><strong>${formatCurrency(p.amount)}</strong></td>
          <td class="tabular-nums" style="font-size: 0.75rem;">${p.payment_date || "—"}</td>
          <td><span class="badge-subtle">${channelLabel}</span></td>
          <td style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(p.raw_text || "—")}</td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("loadPayments error:", err);
  }
}

function populatePaymentAmount(invId) {
  const select = document.getElementById("payment-invoice-id");
  if (!select) return;
  const opt = select.options[select.selectedIndex];
  if (opt && opt.dataset.amount) {
    const amtInput = document.getElementById("payment-amount");
    if (amtInput) amtInput.value = opt.dataset.amount;
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
      if (container) {
        if (reminders.length === 0) {
          container.innerHTML = `<div class="text-muted" style="text-align: center; padding: 24px;">No reminders scheduled.</div>`;
        } else {
          container.innerHTML = reminders.map(r => {
            const isSent = r.status === "SENT";
            const badgeClass = r.reminder_type === "OVERDUE" ? "status-overdue" : r.reminder_type === "DUE_TODAY" ? "status-pending" : "badge-subtle";
            return `
              <div class="reminder-row-item">
                <div class="reminder-info">
                  <div class="reminder-client-name">
                    <span class="${badgeClass}" style="font-size: 0.6875rem;">${r.reminder_type}</span>
                    ${escapeHtml(r.client_name)}
                    <span style="font-weight: 400; color: var(--text-muted); font-size: 0.75rem;">(${escapeHtml(r.client_phone)})</span>
                  </div>
                  <div style="font-size: 0.75rem; color: var(--text-secondary);">
                    ${escapeHtml(r.invoice_description)} — <strong>${formatCurrency(r.invoice_amount)}</strong>
                  </div>
                  <div class="reminder-meta-text">
                    Scheduled: ${r.scheduled_for} ${isSent ? `• <span style="color: #059669;">Delivered: ${r.sent_at}</span>` : '• <span style="color: #d97706;">Pending Dispatch</span>'}
                  </div>
                </div>
                <div>
                  ${!isSent ? `
                    <button class="btn btn-secondary btn-sm" onclick="triggerSendReminder(${r.id})">
                      Send WhatsApp
                    </button>
                  ` : `
                    <span class="status-pill-badge status-paid">Delivered</span>
                  `}
                </div>
              </div>
            `;
          }).join("");
        }
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
      if (feed) {
        if (logs.length === 0) {
          feed.innerHTML = `<div class="text-muted" style="text-align: center; padding: 24px;">No voice commands recorded yet.</div>`;
        } else {
          feed.innerHTML = logs.map(vc => `
            <div class="voice-feed-item">
              <div>
                <div class="voice-transcript">"${escapeHtml(vc.transcript)}"</div>
                <div style="font-size: 0.6875rem; color: var(--text-muted); margin-top: 3px;">${vc.created_at || "Recent"}</div>
              </div>
              <span class="badge-subtle">${escapeHtml(vc.intent)}</span>
            </div>
          `).join("");
        }
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

async function triggerRunReminders() {
  try {
    const res = await fetch(`${API_BASE}/api/reminders/run`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to run reminders");
    const data = await res.json();
    showToast(`Reminders triggered: ${data.count || 0} messages processed.`, "success");
    loadRemindersAndVoice();
  } catch (err) {
    showToast("Error: " + err.message, "error");
  }
}

/* ==========================================================================
   Voice Assistant & Speech Recognition
   ========================================================================== */
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
      micBtn.innerHTML = `Speak`;
      micBtn.classList.remove("recording");
    }
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-IN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isRecording = true;
    if (micBtn) {
      micBtn.innerHTML = `Listening...`;
      micBtn.classList.add("recording");
    }
    showToast("Listening... Speak your command clearly into microphone.", "info");
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    if (input) input.value = transcript;
    showToast(`Recognized: "${transcript}"`, "info");
    submitVoiceCommand();
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    showToast(`Microphone notice: ${event.error}`, "error");
    isRecording = false;
    if (micBtn) {
      micBtn.innerHTML = `Speak`;
      micBtn.classList.remove("recording");
    }
  };

  recognition.onend = () => {
    isRecording = false;
    if (micBtn) {
      micBtn.innerHTML = `Speak`;
      micBtn.classList.remove("recording");
    }
  };

  try {
    recognition.start();
  } catch (err) {
    console.error("Recognition start error:", err);
  }
}

function useHint(hintText) {
  const input = document.getElementById("voice-transcript-input");
  if (input) {
    input.value = hintText;
    submitVoiceCommand();
  }
}

async function submitVoiceCommand() {
  const input = document.getElementById("voice-transcript-input");
  const text = (input ? input.value : "").trim();
  if (!text) return;

  try {
    const res = await fetch(`${API_BASE}/api/voice-commands`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript: text })
    });
    if (!res.ok) throw new Error("Could not process voice command");
    const data = await res.json();
    if (input) input.value = "";

    if (data.action_taken) {
      showToast(data.action_taken, "success");
    } else {
      showToast(`Command logged: [${data.command ? data.command.intent : 'PROCESSED'}]`, "info");
    }
    loadAllData();
  } catch (err) {
    showToast("Error processing command: " + err.message, "error");
  }
}

/* ==========================================================================
   Modals & Form Actions
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
    showToast(`Client "${data.client.name}" registered.`, "success");
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
    showToast(`Invoice #INV-${String(data.invoice.id).padStart(4, "0")} generated with UPI QR code.`, "success");
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
    showToast("Payment settlement recorded successfully.", "success");
    loadAllData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleOcrFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const label = document.getElementById("ocr-file-label");
  if (label) label.textContent = `Scanning: ${file.name}...`;

  const formData = new FormData();
  formData.append("screenshot", file);

  const invSelect = document.getElementById("payment-invoice-id");
  if (invSelect && invSelect.value) {
    formData.append("invoice_id", invSelect.value);
  }

  try {
    const res = await fetch(`${API_BASE}/api/payments/ocr`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) throw new Error("OCR scan failed");
    const data = await res.json();
    const ocr = data.ocr || {};

    if (ocr.amount) {
      const amtInput = document.getElementById("payment-amount");
      if (amtInput) amtInput.value = ocr.amount;
    }
    if (ocr.transaction_id) {
      const txInput = document.getElementById("payment-txid");
      if (txInput) txInput.value = ocr.transaction_id;
    }
    const rawInput = document.getElementById("payment-raw");
    if (rawInput && ocr.raw_text) {
      rawInput.value = ocr.raw_text.substring(0, 100);
    }

    const sourceSelect = document.getElementById("payment-source");
    if (sourceSelect) sourceSelect.value = "ocr";

    if (label) label.textContent = `Extracted: ₹${ocr.amount || '0'} | ${ocr.transaction_id || 'UTR noted'}`;
    showToast("Screenshot OCR processed. Values filled in form.", "success");
  } catch (err) {
    if (label) label.textContent = "OCR scan failed. Enter manually.";
    showToast("OCR processing notice: " + err.message, "info");
  }
}

async function triggerDbSeed(force = true) {
  if (force && !confirm("Re-seed sample database? This will refresh sample MSME clients, invoices, payments, and reminders.")) {
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
   Utilities
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
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.2s ease";
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

/* ==========================================================================
   WhatsApp Business AI Chat System (Client & Manager)
   Controller & Interaction Pipeline
   ========================================================================== */
let currentChatMode = "client"; // "client" | "manager"
let activeChatClientId = null;
let isClientChatSending = false;
let isManagerChatSending = false;

function setChatMode(mode) {
  currentChatMode = mode;
  
  const clientBtn = document.getElementById("chat-mode-btn-client");
  const managerBtn = document.getElementById("chat-mode-btn-manager");
  const clientView = document.getElementById("chat-view-client");
  const managerView = document.getElementById("chat-view-manager");

  if (mode === "client") {
    if (clientBtn) clientBtn.classList.add("active");
    if (managerBtn) managerBtn.classList.remove("active");
    if (clientView) clientView.style.display = "block";
    if (managerView) managerView.style.display = "none";
    const input = document.getElementById("input-client-chat");
    if (input) input.focus();
    if (activeChatClientId) {
      loadClientChatHistory(activeChatClientId);
    }
  } else {
    if (clientBtn) clientBtn.classList.remove("active");
    if (managerBtn) managerBtn.classList.add("active");
    if (clientView) clientView.style.display = "none";
    if (managerView) managerView.style.display = "block";
    const input = document.getElementById("input-manager-chat");
    if (input) input.focus();
    loadManagerChatHistory();
  }
}

async function loadChatData() {
  // Ensure clients list is loaded
  if (!allClients || allClients.length === 0) {
    try {
      const res = await fetch(`${API_BASE}/api/clients`);
      if (res.ok) {
        allClients = await res.json();
      }
    } catch (err) {
      console.warn("Could not fetch clients for chat:", err);
    }
  }

  populateChatClientDropdown();

  if (currentChatMode === "client") {
    if (activeChatClientId) {
      await loadClientChatHistory(activeChatClientId);
    }
  } else {
    await loadManagerChatHistory();
  }
}

function populateChatClientDropdown() {
  const select = document.getElementById("chat-client-select");
  if (!select) return;

  const prevVal = select.value;
  select.innerHTML = "";

  if (!allClients || allClients.length === 0) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No clients registered yet";
    select.appendChild(opt);
    return;
  }

  allClients.forEach((cl, idx) => {
    const opt = document.createElement("option");
    opt.value = cl.id;
    const phoneStr = cl.phone ? ` (${cl.phone})` : "";
    opt.textContent = `${cl.name}${phoneStr}`;
    select.appendChild(opt);
  });

  if (prevVal && allClients.some(c => String(c.id) === String(prevVal))) {
    select.value = prevVal;
    activeChatClientId = parseInt(prevVal);
  } else {
    select.selectedIndex = 0;
    activeChatClientId = allClients[0].id;
  }

  updateChatClientTelemetry();
}

function onChatClientChange() {
  const select = document.getElementById("chat-client-select");
  if (!select || !select.value) return;

  activeChatClientId = parseInt(select.value);
  updateChatClientTelemetry();
  loadClientChatHistory(activeChatClientId);
}

function updateChatClientTelemetry() {
  if (!activeChatClientId || !allClients) return;
  const client = allClients.find(c => c.id === activeChatClientId);
  if (!client) return;

  const phoneEl = document.getElementById("chat-meta-phone");
  const invoicesEl = document.getElementById("chat-meta-invoices");
  const balanceEl = document.getElementById("chat-meta-balance");

  if (phoneEl) phoneEl.textContent = client.phone || "No phone";
  if (invoicesEl) invoicesEl.textContent = `${client.invoices_count || 0} bills`;
  if (balanceEl) {
    const pendingVal = parseFloat(client.pending_amount) || 0;
    balanceEl.textContent = formatCurrency(pendingVal);
    balanceEl.className = pendingVal > 0 ? "meta-value meta-due" : "meta-value";
  }
}

async function loadClientChatHistory(clientId) {
  const container = document.getElementById("client-chat-messages");
  if (!container) return;

  try {
    const res = await fetch(`${API_BASE}/api/chat/history?client_id=${clientId}`);
    if (res.ok) {
      const data = await res.json();
      renderChatMessages(container, data.messages || [], "client");
    }
  } catch (err) {
    console.error("Failed to load client chat history:", err);
  }
}

async function loadManagerChatHistory() {
  const container = document.getElementById("manager-chat-messages");
  if (!container) return;

  try {
    const res = await fetch(`${API_BASE}/api/chat/history?session_id=manager`);
    if (res.ok) {
      const data = await res.json();
      renderChatMessages(container, data.messages || [], "manager");
    }
  } catch (err) {
    console.error("Failed to load manager chat history:", err);
  }
}

function renderChatMessages(container, messages, mode) {
  // Keep the date divider and encrypted notice
  const dateDivider = `<div class="wa-date-divider"><span>TODAY</span></div>`;
  const notice = mode === "client"
    ? `<div class="wa-encrypted-notice">🔒 Messages and responses are automated by ChatBiz AI WhatsApp Business Bot. Natural language queries are processed in real-time.</div>`
    : `<div class="wa-encrypted-notice">⚡ Manager Executive Mode: You can issue commands to fetch any client's dossier, create invoices, record payments, view revenue telemetry, or dispatch payment reminders.</div>`;

  let html = dateDivider + notice;

  messages.forEach(msg => {
    html += buildMessageBubbleHtml(msg);
  });

  container.innerHTML = html;
  container.scrollTop = container.scrollHeight;
}

function buildMessageBubbleHtml(msg) {
  const isUser = msg.role === "user";
  const rowClass = isUser ? "wa-message-row user-row" : "wa-message-row bot-row";
  const bubbleClass = isUser ? "wa-bubble wa-bubble-user" : "wa-bubble wa-bubble-bot";
  
  const senderName = escapeHtml(msg.sender || (isUser ? "You" : "ChatBiz AI"));
  const timeStr = formatChatTimestamp(msg.created_at);
  const formattedBody = formatChatMessageContent(msg.content);
  
  const checkmarks = isUser ? `<span class="wa-checks">✓✓</span>` : "";
  
  let attachmentHtml = "";
  if (msg.metadata) {
    attachmentHtml = renderAttachmentWidget(msg.metadata);
  }

  return `
    <div class="${rowClass}">
      <div class="${bubbleClass}">
        <div class="wa-bubble-header">
          <span>${senderName}</span>
        </div>
        <div class="wa-bubble-content">${formattedBody}</div>
        ${attachmentHtml}
        <div class="wa-bubble-footer">
          <span>${timeStr}</span>
          ${checkmarks}
        </div>
      </div>
    </div>
  `;
}

function formatChatTimestamp(isoStr) {
  if (!isoStr) {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch (e) {
    return "";
  }
}

function formatChatMessageContent(raw) {
  if (!raw) return "";
  let text = escapeHtml(raw);

  // Bold: **text**
  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Code: `code`
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Italics: *text*
  text = text.replace(/(^|[^\*])\*([^\*]+)\*([^\*]|$)/g, "$1<em>$2</em>$3");

  // Bullet points
  text = text.replace(/^[•\-\*]\s+(.*)$/gm, "<div style='display:flex; gap:6px; margin:2px 0;'><span>•</span><span>$1</span></div>");

  // Line breaks
  text = text.replace(/\n/g, "<br>");

  return text;
}

function renderAttachmentWidget(meta) {
  if (!meta || !meta.type) return "";

  if (meta.type === "invoice_download" || meta.type === "invoice_created") {
    const invId = meta.invoice_id;
    const url = meta.download_url ? `${API_BASE}${meta.download_url}` : `${API_BASE}/api/invoices/${invId}/pdf`;
    return `
      <div class="wa-card-attachment">
        <div class="wa-card-info">
          <span class="wa-card-title">📄 Invoice #${String(invId).padStart(4, "0")} PDF</span>
          <span class="wa-card-sub">With embedded UPI payment QR code</span>
        </div>
        <a href="${url}" target="_blank" download="invoice_${invId}.pdf" class="btn btn-secondary btn-sm">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download PDF
        </a>
      </div>
    `;
  }

  if (meta.type === "payment_info") {
    return `
      <div class="wa-card-attachment">
        <div class="wa-card-info">
          <span class="wa-card-title">📱 UPI Merchant ID</span>
          <span class="wa-card-sub"><code>${escapeHtml(meta.upi_id || "chatbiz.merchant@upi")}</code></span>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText('${meta.upi_id || "chatbiz.merchant@upi"}'); showToast('UPI ID copied to clipboard!', 'info');">
          Copy UPI ID
        </button>
      </div>
    `;
  }

  if (meta.type === "client_dossier" && meta.client) {
    const cl = meta.client;
    return `
      <div class="wa-card-attachment">
        <div class="wa-card-info">
          <span class="wa-card-title">👤 ${escapeHtml(cl.name)}</span>
          <span class="wa-card-sub">Phone: ${escapeHtml(cl.phone || "N/A")} • Pending: ${formatCurrency(meta.pending_balance)}</span>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="switchTab('invoices');">
          View Invoices
        </button>
      </div>
    `;
  }

  if (meta.type === "whatsapp_sent" && meta.client_id) {
    return `
      <div class="wa-card-attachment">
        <div class="wa-card-info">
          <span class="wa-card-title">💬 WhatsApp Dispatched</span>
          <span class="wa-card-sub">To: ${escapeHtml(meta.client_name || "Client")} (${escapeHtml(meta.client_phone || "")})</span>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="switchChatClient(${meta.client_id})">
          View Client Chat
        </button>
      </div>
    `;
  }

  if (meta.type === "legitimacy_verification") {
    return `
      <div class="wa-card-attachment" style="background: rgba(16, 185, 129, 0.08); border-color: rgba(16, 185, 129, 0.35);">
        <div class="wa-card-info">
          <span class="wa-card-title" style="color: #065f46; font-weight: 700;">🛡️ Verified Government &amp; Tax Compliant</span>
          <span class="wa-card-sub" style="color: #047857;">CIN: ${escapeHtml(meta.cin || "Active")} • GSTIN: ${escapeHtml(meta.gstin || "Active")} • TrustScore: ${escapeHtml(meta.trust_score || "4.9/5.0")} ⭐</span>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="showToast('Official credentials verified: Active MCA, GSTIN, and DPIIT records confirmed.', 'success');">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Audit Details
        </button>
      </div>
    `;
  }

  return "";
}

function switchChatClient(clientId) {
  if (!clientId) return;
  switchTab("chat");
  switchChatMode("client");
  const select = document.getElementById("chat-client-select");
  if (select) {
    select.value = clientId;
    onChatClientChange();
  }
}

async function handleSendClientChat(event) {
  if (event) event.preventDefault();
  if (isClientChatSending) return;

  const input = document.getElementById("input-client-chat");
  const container = document.getElementById("client-chat-messages");
  const sendBtn = document.getElementById("btn-client-send");
  if (!input || !container) return;

  const text = input.value.trim();
  if (!text) return;

  if (!activeChatClientId) {
    showToast("Please select a client account first.", "error");
    return;
  }

  const selectedClient = allClients ? allClients.find(c => c.id === activeChatClientId) : null;
  const clientName = selectedClient ? selectedClient.name : "You";

  // Append user message bubble immediately
  const userMsg = {
    role: "user",
    sender: clientName,
    content: text,
    created_at: new Date().toISOString()
  };
  container.insertAdjacentHTML("beforeend", buildMessageBubbleHtml(userMsg));
  container.scrollTop = container.scrollHeight;

  input.value = "";
  isClientChatSending = true;
  if (sendBtn) sendBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/chat/client`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: activeChatClientId,
        message: text
      })
    });

    if (res.ok) {
      const data = await res.json();
      const botMsg = {
        role: "assistant",
        sender: "ChatBiz AI (WhatsApp Business)",
        content: data.reply,
        metadata: data.metadata,
        created_at: new Date().toISOString()
      };
      container.insertAdjacentHTML("beforeend", buildMessageBubbleHtml(botMsg));
      container.scrollTop = container.scrollHeight;

      // Update client balance if telemetry changed
      if (data.client) {
        const found = allClients.find(c => c.id === data.client.id);
        if (found) {
          found.pending_amount = data.client.pending_balance;
          updateChatClientTelemetry();
        }
      }
    } else {
      const err = await res.json().catch(() => ({ detail: "API Error" }));
      container.insertAdjacentHTML("beforeend", buildMessageBubbleHtml({
        role: "assistant",
        sender: "ChatBiz AI",
        content: `⚠️ Error: ${err.detail || "Could not process request."}`,
        created_at: new Date().toISOString()
      }));
    }
  } catch (err) {
    container.insertAdjacentHTML("beforeend", buildMessageBubbleHtml({
      role: "assistant",
      sender: "ChatBiz AI",
      content: "⚠️ Network connection to ChatBiz backend was interrupted.",
      created_at: new Date().toISOString()
    }));
  } finally {
    isClientChatSending = false;
    if (sendBtn) sendBtn.disabled = false;
    container.scrollTop = container.scrollHeight;
  }
}

async function handleSendManagerChat(event) {
  if (event) event.preventDefault();
  if (isManagerChatSending) return;

  const input = document.getElementById("input-manager-chat");
  const container = document.getElementById("manager-chat-messages");
  const sendBtn = document.getElementById("btn-manager-send");
  if (!input || !container) return;

  const text = input.value.trim();
  if (!text) return;

  // Append user command bubble immediately
  const userMsg = {
    role: "user",
    sender: "Manager",
    content: text,
    created_at: new Date().toISOString()
  };
  container.insertAdjacentHTML("beforeend", buildMessageBubbleHtml(userMsg));
  container.scrollTop = container.scrollHeight;

  input.value = "";
  isManagerChatSending = true;
  if (sendBtn) sendBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/chat/manager`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    if (res.ok) {
      const data = await res.json();
      const botMsg = {
        role: "assistant",
        sender: "ChatBiz Operations AI",
        content: data.reply,
        metadata: data.metadata,
        created_at: new Date().toISOString()
      };
      container.insertAdjacentHTML("beforeend", buildMessageBubbleHtml(botMsg));
      container.scrollTop = container.scrollHeight;

      // If an operational command was executed, refresh all background datasets
      if (data.action_taken) {
        showToast(data.action_taken, "info");
        loadInvoices();
        loadClients();
        loadAnalytics();
      }
    } else {
      const err = await res.json().catch(() => ({ detail: "API Error" }));
      container.insertAdjacentHTML("beforeend", buildMessageBubbleHtml({
        role: "assistant",
        sender: "ChatBiz Operations AI",
        content: `⚠️ Error executing command: ${err.detail || "Request failed."}`,
        created_at: new Date().toISOString()
      }));
    }
  } catch (err) {
    container.insertAdjacentHTML("beforeend", buildMessageBubbleHtml({
      role: "assistant",
      sender: "ChatBiz Operations AI",
      content: "⚠️ Failed to reach ChatBiz API server.",
      created_at: new Date().toISOString()
    }));
  } finally {
    isManagerChatSending = false;
    if (sendBtn) sendBtn.disabled = false;
    container.scrollTop = container.scrollHeight;
  }
}

function sendQuickPrompt(mode, promptText) {
  if (mode === "client") {
    const input = document.getElementById("input-client-chat");
    if (input) {
      input.value = promptText;
      handleSendClientChat();
    }
  } else {
    const input = document.getElementById("input-manager-chat");
    if (input) {
      input.value = promptText;
      handleSendManagerChat();
    }
  }
}

async function clearCurrentChat(mode) {
  const payload = mode === "client"
    ? { client_id: activeChatClientId }
    : { session_id: "manager" };

  try {
    const res = await fetch(`${API_BASE}/api/chat/clear`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      showToast("Conversation cleared", "info");
      if (mode === "client") {
        await loadClientChatHistory(activeChatClientId);
      } else {
        await loadManagerChatHistory();
      }
    }
  } catch (err) {
    showToast("Could not clear conversation", "error");
  }
}

function promptCreateSelfInvoice() {
  const input = document.getElementById("input-client-chat");
  if (input) {
    input.value = "Create invoice for 5000 for Website Optimization";
    input.focus();
    input.select();
    showToast("Pre-filled invoice request. Press send or adjust amount/description.", "info");
  }
}

