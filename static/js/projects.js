const grid = document.querySelector('#projects-grid');
const i18n = window.CAD_I18N;
const t = (key, values) => i18n.t(key, values);
let loadedProjects = [];

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function formatDate(iso) {
  if (!iso) return '—';
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffDays === 0) return t('projects.today');
  if (diffDays === 1) return t('projects.yesterday');
  if (diffDays < 7) return t('projects.daysAgo', {count: diffDays});
  const locale = i18n.getLanguage() === 'zh-CN' ? 'zh-CN' : 'en-US';
  return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' });
}

function statusLabel(status) {
  const translated = t(`projects.status.${status}`);
  return translated === `projects.status.${status}` ? status : translated;
}

function statusClass(status) {
  return `status-${status}`;
}

function cardTemplate(project) {
  return `
    <div class="project-card" data-name="${escapeHTML(project.name)}">
      <a href="/project/${encodeURIComponent(project.name)}" class="card-main">
        <h3 class="card-name">${escapeHTML(project.name)}</h3>
        <div class="card-meta">
          <span class="card-date">${escapeHTML(t('projects.created', {date: formatDate(project.created_at)}))}</span>
          <span class="card-date">${escapeHTML(t('projects.modified', {date: formatDate(project.modified_at)}))}</span>
        </div>
        <span class="model-badge ${statusClass(project.model_status)}">${statusLabel(project.model_status)}</span>
      </a>
      <div class="card-actions">
        <button class="icon-btn rename-btn" title="${escapeHTML(t('projects.rename'))}" data-name="${escapeHTML(project.name)}" aria-label="${escapeHTML(t('projects.rename'))} ${escapeHTML(project.name)}">✏️</button>
        <button class="icon-btn delete-btn" title="${escapeHTML(t('projects.delete'))}" data-name="${escapeHTML(project.name)}" aria-label="${escapeHTML(t('projects.delete'))} ${escapeHTML(project.name)}">🗑️</button>
      </div>
    </div>
  `;
}

function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

async function loadProjects() {
  try {
    const data = await api('/api/projects');
    loadedProjects = data.projects || [];
    renderProjects(data.projects);
  } catch (error) {
    grid.innerHTML = `<div class="empty-projects"><p class="error">${escapeHTML(t('projects.loadFailed', {error: error.message}))}</p></div>`;
  }
}

function renderProjects(projects) {
  if (!projects.length) {
    grid.innerHTML = `
      <div class="empty-projects">
        <div class="empty-icon">◇</div>
        <h2>${escapeHTML(t('projects.emptyTitle'))}</h2>
        <p>${escapeHTML(t('projects.emptyText'))}</p>
        <button id="empty-cta" class="primary">${escapeHTML(t('projects.getStarted'))}</button>
      </div>
    `;
    document.querySelector('#empty-cta')?.addEventListener('click', openNewProjectModal);
    return;
  }
  grid.innerHTML = projects.map(cardTemplate).join('');
  grid.querySelectorAll('.rename-btn').forEach(btn => {
    btn.addEventListener('click', () => openRenameModal(btn.dataset.name));
  });
  grid.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', () => openDeleteConfirm(btn.dataset.name));
  });
}

/* ── New Project Modal ── */

const newProjectModal = document.querySelector('#new-project-modal');
const newProjectForm = document.querySelector('#new-project-form');
const newProjectName = document.querySelector('#new-project-name');

function openNewProjectModal() {
  newProjectModal.classList.remove('hidden');
  newProjectName.value = '';
  newProjectName.focus();
}

document.querySelector('#new-project-btn').addEventListener('click', openNewProjectModal);
document.querySelector('#empty-cta')?.addEventListener('click', openNewProjectModal);
document.querySelector('#cancel-new-project').addEventListener('click', () => {
  newProjectModal.classList.add('hidden');
});

newProjectForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const rawName = newProjectName.value.trim();
  const name = rawName.toLowerCase().replace(/\s+/g, '-');
  if (!name) return;
  try {
    await api('/api/projects/new', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    window.location.href = `/project/${encodeURIComponent(name)}`;
  } catch (error) {
    alert(error.message);
  }
});

/* ── Rename Modal ── */

const renameModal = document.querySelector('#rename-modal');
const renameForm = document.querySelector('#rename-form');
const renameName = document.querySelector('#rename-name');
let renameTarget = '';

function openRenameModal(name) {
  renameTarget = name;
  renameName.value = name;
  renameModal.classList.remove('hidden');
  renameName.focus();
  renameName.select();
}

document.querySelector('#cancel-rename').addEventListener('click', () => {
  renameModal.classList.add('hidden');
});

renameForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const rawName = renameName.value.trim();
  const newName = rawName.toLowerCase().replace(/\s+/g, '-');
  if (!newName || newName === renameTarget) {
    renameModal.classList.add('hidden');
    return;
  }
  try {
    await api(`/api/projects/${encodeURIComponent(renameTarget)}/rename`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName }),
    });
    renameModal.classList.add('hidden');
    await loadProjects();
  } catch (error) {
    alert(error.message);
  }
});

/* ── Delete Confirm ── */

const deleteModal = document.querySelector('#delete-confirm');
const deleteConfirmText = document.querySelector('#delete-confirm-text');
let deleteTarget = '';

function openDeleteConfirm(name) {
  deleteTarget = name;
  deleteConfirmText.textContent = t('projects.deleteConfirm', {name});
  deleteModal.classList.remove('hidden');
}

document.querySelector('#cancel-delete').addEventListener('click', () => {
  deleteModal.classList.add('hidden');
});

document.querySelector('#confirm-delete').addEventListener('click', async () => {
  try {
    await api(`/api/projects/${encodeURIComponent(deleteTarget)}`, { method: 'DELETE' });
    deleteModal.classList.add('hidden');
    await loadProjects();
  } catch (error) {
    alert(error.message);
  }
});

/* ── Init ── */

loadProjects();

window.addEventListener('cad-language-change', () => {
  i18n.applyTranslations();
  renderProjects(loadedProjects);
  if (!deleteModal.classList.contains('hidden') && deleteTarget) {
    deleteConfirmText.textContent = t('projects.deleteConfirm', {name: deleteTarget});
  }
});
