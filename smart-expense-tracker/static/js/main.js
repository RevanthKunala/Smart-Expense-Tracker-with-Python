/**
 * main.js — Sidebar toggle, dark mode, password toggle, delete modal, alerts.
 */

document.addEventListener("DOMContentLoaded", () => {
  initDarkMode();
  initSidebar();
  initPasswordToggle();
  initDeleteModal();
  initAutoDismissAlerts();
});

/* ── Dark Mode ────────────────────────────────────────────────── */
function initDarkMode() {
  const btn = document.getElementById("darkToggle");
  const root = document.documentElement;
  const saved = localStorage.getItem("theme") || "light";
  root.setAttribute("data-theme", saved);
  updateDarkIcon(btn, saved);

  btn?.addEventListener("click", () => {
    const current = root.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    updateDarkIcon(btn, next);
  });
}

function updateDarkIcon(btn, theme) {
  if (!btn) return;
  btn.textContent = theme === "dark" ? "☀️" : "🌙";
  btn.title = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
}

/* ── Sidebar ──────────────────────────────────────────────────── */
function initSidebar() {
  const toggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebarOverlay");

  function openSidebar() {
    sidebar?.classList.add("open");
    overlay?.classList.add("visible");
  }
  function closeSidebar() {
    sidebar?.classList.remove("open");
    overlay?.classList.remove("visible");
  }

  toggle?.addEventListener("click", () => {
    sidebar?.classList.contains("open") ? closeSidebar() : openSidebar();
  });
  overlay?.addEventListener("click", closeSidebar);
}

/* ── Password Toggle ──────────────────────────────────────────── */
function initPasswordToggle() {
  document.querySelectorAll(".password-toggle").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = btn.previousElementSibling;
      if (!input) return;
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      btn.textContent = isPassword ? "🙈" : "👁️";
    });
  });
}

/* ── Delete Modal ─────────────────────────────────────────────── */
function initDeleteModal() {
  const modal = document.getElementById("deleteModal");
  const form = document.getElementById("deleteForm");
  const cancel = document.getElementById("cancelDelete");

  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn-delete");
    if (!btn) return;
    const url = btn.dataset.deleteUrl;
    if (!url) return;
    form.action = url;
    modal?.classList.add("open");
  });

  cancel?.addEventListener("click", () => modal?.classList.remove("open"));
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("open");
  });
}

/* ── Auto-dismiss alerts ──────────────────────────────────────── */
function initAutoDismissAlerts() {
  document.querySelectorAll(".alert").forEach(alert => {
    setTimeout(() => {
      alert.style.transition = "opacity .5s ease, max-height .5s ease";
      alert.style.opacity = "0";
      alert.style.maxHeight = "0";
      alert.style.overflow = "hidden";
      setTimeout(() => alert.remove(), 500);
    }, 4500);
  });
}
