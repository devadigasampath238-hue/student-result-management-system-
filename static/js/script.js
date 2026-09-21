/* =========================================================
   Student Result Management System — Frontend JS
   Theme toggle, sidebar, toasts, search, validation, counters
   ========================================================= */

document.addEventListener('DOMContentLoaded', () => {
  hidePageLoader();
  initThemeToggle();
  initSidebarToggle();
  showFlashesAsToasts();
  initCountUp();
  initLiveSearch();
  initFormValidation();
  initPasswordToggle();
  initConfirmDialogs();
  initTableSearch('#marksSearch', '#marksTable');
  initTableSearch('#resultsSearch', '#resultsTable');
});

/* ---------------- Page loader ---------------- */
function hidePageLoader() {
  const loader = document.getElementById('loader');
  if (!loader) return;
  window.addEventListener('load', () => {
    setTimeout(() => loader.classList.add('hidden'), 200);
  });
  // Fallback in case 'load' already fired
  setTimeout(() => loader.classList.add('hidden'), 800);
}

/* ---------------- Theme toggle (dark/light) ---------------- */
function initThemeToggle() {
  const toggle = document.getElementById('themeToggle');
  const html = document.documentElement;
  const saved = getStoredTheme();
  if (saved) {
    html.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
  }
  if (!toggle) return;
  toggle.addEventListener('click', () => {
    const current = html.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    storeTheme(next);
    updateThemeIcon(next);
  });
}
function updateThemeIcon(theme) {
  const toggle = document.getElementById('themeToggle');
  if (!toggle) return;
  const icon = toggle.querySelector('i');
  if (icon) icon.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
}
// In-memory theme store (artifacts/sandboxed views can't use localStorage,
// but this is a standalone Flask app so localStorage is safe here).
function storeTheme(t) { try { localStorage.setItem('srms_theme', t); } catch (e) {} }
function getStoredTheme() { try { return localStorage.getItem('srms_theme'); } catch (e) { return null; } }

/* ---------------- Sidebar toggle (mobile + collapse) ---------------- */
function initSidebarToggle() {
  const btn = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (!btn || !sidebar) return;
  btn.addEventListener('click', () => {
    if (window.innerWidth <= 780) {
      sidebar.classList.toggle('open');
    } else {
      sidebar.classList.toggle('collapsed');
    }
  });
}

/* ---------------- Toast notifications ---------------- */
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const icons = { success: 'fa-circle-check', error: 'fa-circle-exclamation', warning: 'fa-triangle-exclamation' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i class="fa-solid ${icons[type] || icons.success}"></i><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('fade-out');
    setTimeout(() => toast.remove(), 350);
  }, 3500);
}

function showFlashesAsToasts() {
  document.querySelectorAll('.flash').forEach(el => {
    const type = el.classList.contains('flash-success') ? 'success'
      : el.classList.contains('flash-error') ? 'error' : 'warning';
    const text = el.querySelector('span')?.textContent || '';
    if (text) showToast(text, type);
  });
}

/* ---------------- Animated stat counters ---------------- */
function initCountUp() {
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseFloat(el.getAttribute('data-count')) || 0;
    const isDecimal = target % 1 !== 0;
    let current = 0;
    const steps = 40;
    const increment = target / steps;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      el.textContent = isDecimal ? current.toFixed(1) : Math.round(current);
    }, 20);
  });
}

/* ---------------- Live search (students page -> server side, debounced) ---------------- */
function initLiveSearch() {
  const input = document.getElementById('liveSearch');
  if (!input) return;
  let timer;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => input.form.submit(), 500);
  });
}

/* ---------------- Client-side table search (marks / results pages) ---------------- */
function initTableSearch(inputSelector, tableSelector) {
  const input = document.querySelector(inputSelector);
  const table = document.querySelector(tableSelector);
  if (!input || !table) return;
  input.addEventListener('input', () => {
    const term = input.value.toLowerCase();
    table.querySelectorAll('tbody tr').forEach(row => {
      row.style.display = row.textContent.toLowerCase().includes(term) ? '' : 'none';
    });
  });
}

/* ---------------- Form validation ---------------- */
function initFormValidation() {
  document.querySelectorAll('form.js-validate').forEach(form => {
    form.addEventListener('submit', (e) => {
      let valid = true;
      form.querySelectorAll('[required]').forEach(field => {
        if (!field.value || !field.value.trim()) {
          valid = false;
          field.classList.add('invalid');
        } else {
          field.classList.remove('invalid');
        }
      });

      const email = form.querySelector('input[type="email"]');
      if (email && email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
        valid = false;
        email.classList.add('invalid');
      }

      const newPw = form.querySelector('#new_password');
      const confirmPw = form.querySelector('#confirm_password');
      if (newPw && confirmPw && newPw.value !== confirmPw.value) {
        valid = false;
        confirmPw.classList.add('invalid');
        showToast('New passwords do not match.', 'error');
      }

      if (!valid) {
        e.preventDefault();
        showToast('Please fill in all required fields correctly.', 'error');
      }
    });

    form.querySelectorAll('input, select').forEach(field => {
      field.addEventListener('input', () => field.classList.remove('invalid'));
    });
  });
}

/* ---------------- Password show/hide ---------------- */
function initPasswordToggle() {
  document.querySelectorAll('.toggle-pw').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.previousElementSibling;
      if (!input) return;
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      const icon = btn.querySelector('i');
      if (icon) icon.className = isPassword ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye';
    });
  });
}

/* ---------------- Confirmation dialogs ---------------- */
function initConfirmDialogs() {
  document.querySelectorAll('.confirm-delete').forEach(form => {
    form.addEventListener('submit', (e) => {
      if (!confirm('Are you sure you want to delete this record? This action cannot be undone.')) {
        e.preventDefault();
      }
    });
  });
  document.querySelectorAll('.confirm-restore').forEach(form => {
    form.addEventListener('submit', (e) => {
      if (!confirm('Restoring will overwrite the current database. Continue?')) {
        e.preventDefault();
      }
    });
  });
}
