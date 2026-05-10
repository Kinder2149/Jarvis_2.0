(function() {
  let currentProjectId = null;
  let currentProject = null;

  window.initExplorer = async function(projectId) {
    currentProjectId = projectId;

    try {
      currentProject = await window.API.getProject(projectId);

      if (!currentProject.path || !currentProject.path.trim()) {
        renderNoFolder();
        return;
      }

      await renderExplorer();
      await loadFileTree();
      restoreCollapseState();

    } catch (error) {
      console.error('Erreur initialisation explorateur:', error);
    }
  };

  function renderNoFolder() {
    const explorer = document.getElementById('explorer');
    if (!explorer) return;

    explorer.classList.add('explorer--hidden');
    explorer.innerHTML = `
      <div class="explorer-container">
        <div class="explorer-header">
          <span class="explorer-title">📂 Fichiers</span>
        </div>
        <div style="padding:1rem;color:var(--text-muted);text-align:center;font-size:0.85rem">
          Aucun dossier lié.<br>Aller dans le projet pour en ajouter un.
        </div>
      </div>
    `;
  }

  async function renderExplorer() {
    const explorer = document.getElementById('explorer');
    if (!explorer) return;

    explorer.classList.remove('explorer--hidden');

    const pathDisplay = currentProject.path.length > 40
      ? '...' + currentProject.path.slice(-40)
      : currentProject.path;

    explorer.innerHTML = `
      <div class="explorer-container">
        <div class="explorer-header">
          <span class="explorer-title">📂 Fichiers</span>
          <div class="explorer-header-actions">
            <button id="btn-graphify" class="btn-icon" title="Analyser avec Graphify">🗺️</button>
            <button id="btn-explorer-collapse" class="btn-icon" title="Fermer">→</button>
          </div>
        </div>

        <div class="explorer-path" id="explorer-path" title="${currentProject.path}">
          ${pathDisplay}
        </div>

        <div class="explorer-tree" id="explorer-tree">
          <p style="color:var(--text-muted);padding:1rem;text-align:center">Chargement...</p>
        </div>

        <div class="explorer-preview" id="explorer-preview" style="display:none">
          <div class="explorer-preview-header">
            <span id="explorer-preview-filename"></span>
            <button id="btn-close-preview" class="btn-icon">✕</button>
          </div>
          <pre id="explorer-preview-content"></pre>
        </div>
      </div>
    `;

    attachExplorerHandlers();
  }

  function attachExplorerHandlers() {
    const btnCollapse = document.getElementById('btn-explorer-collapse');
    const btnGraphify = document.getElementById('btn-graphify');
    const btnClosePreview = document.getElementById('btn-close-preview');

    if (btnCollapse) {
      btnCollapse.addEventListener('click', collapseExplorer);
    }

    if (btnGraphify) {
      btnGraphify.addEventListener('click', () => {
        if (window.showToast) window.showToast('Graphify — Fonctionnalité à venir');
        console.log('Graphify clicked for project:', currentProjectId);
      });
    }

    if (btnClosePreview) {
      btnClosePreview.addEventListener('click', closePreview);
    }
  }

  function collapseExplorer() {
    const explorer = document.getElementById('explorer');
    if (!explorer) return;

    explorer.classList.add('explorer--hidden');
    localStorage.setItem('explorer_hidden', 'true');

    injectToggleButton();
  }

  function injectToggleButton() {
    if (document.getElementById('btn-open-explorer')) return;

    const headers = [
      document.querySelector('.mc-header'),
      document.querySelector('.chat-header'),
      document.querySelector('.project-header')
    ];

    const header = headers.find(h => h !== null);
    if (!header) return;

    const btn = document.createElement('button');
    btn.id = 'btn-open-explorer';
    btn.className = 'btn-icon explorer-toggle-btn';
    btn.title = 'Ouvrir explorateur';
    btn.textContent = '📂';
    btn.style.marginLeft = '8px';
    btn.addEventListener('click', expandExplorer);

    const headerRight = header.querySelector('.mc-header-info, .chat-header-left, .project-header-main');
    if (headerRight) {
      headerRight.appendChild(btn);
    } else {
      header.appendChild(btn);
    }
  }

  function expandExplorer() {
    const explorer = document.getElementById('explorer');
    if (!explorer) return;

    explorer.classList.remove('explorer--hidden');
    localStorage.setItem('explorer_hidden', 'false');

    const btn = document.getElementById('btn-open-explorer');
    if (btn) btn.remove();
  }

  function restoreCollapseState() {
    const isHidden = localStorage.getItem('explorer_hidden') === 'true';
    if (isHidden) {
      collapseExplorer();
    }
  }

  async function loadFileTree() {
    try {
      const files = await window.API.listLocalFiles(currentProjectId);
      const tree = buildTree(files);
      renderTree(tree);
    } catch (error) {
      console.error('Erreur chargement arborescence:', error);
      const container = document.getElementById('explorer-tree');
      if (container) {
        container.innerHTML = '<p style="color:var(--danger);padding:1rem;text-align:center">Erreur de chargement</p>';
      }
    }
  }

  function buildTree(paths) {
    const tree = {};

    paths.forEach(path => {
      const parts = path.split(/[\/\\]/);
      let current = tree;

      parts.forEach((part, index) => {
        if (index === parts.length - 1) {
          current[part] = null;
        } else {
          if (!current[part]) {
            current[part] = {};
          }
          current = current[part];
        }
      });
    });

    return tree;
  }

  function renderTree(tree) {
    const container = document.getElementById('explorer-tree');
    if (!container) return;

    container.innerHTML = '';
    renderTreeNode(tree, container, 0, '');
  }

  function renderTreeNode(node, container, depth, currentPath) {
    const entries = Object.entries(node).sort((a, b) => {
      const aIsFolder = a[1] !== null;
      const bIsFolder = b[1] !== null;
      if (aIsFolder && !bIsFolder) return -1;
      if (!aIsFolder && bIsFolder) return 1;
      return a[0].localeCompare(b[0]);
    });

    entries.forEach(([name, children]) => {
      const fullPath = currentPath ? `${currentPath}/${name}` : name;

      if (children === null) {
        const fileEl = document.createElement('div');
        fileEl.className = 'tree-file';
        fileEl.dataset.path = fullPath;
        fileEl.style.paddingLeft = `${depth * 12 + 8}px`;
        fileEl.innerHTML = `${getFileIcon(name)} ${name}`;
        fileEl.addEventListener('click', () => handleFileClick(fileEl, fullPath));
        container.appendChild(fileEl);
      } else {
        const folderEl = document.createElement('div');
        folderEl.className = 'tree-folder';

        const folderName = document.createElement('div');
        folderName.className = 'tree-folder-name';
        folderName.style.paddingLeft = `${depth * 12}px`;
        folderName.innerHTML = `<span class="tree-folder-arrow">▶</span> 📁 ${name}`;

        const folderChildren = document.createElement('div');
        folderChildren.className = 'tree-folder-children';
        folderChildren.style.display = 'none';

        folderName.addEventListener('click', () => toggleFolder(folderEl, folderName, folderChildren));

        folderEl.appendChild(folderName);
        folderEl.appendChild(folderChildren);
        container.appendChild(folderEl);

        renderTreeNode(children, folderChildren, depth + 1, fullPath);
      }
    });
  }

  function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
      'py': '🐍',
      'js': '📜',
      'html': '🌐',
      'css': '🎨',
      'md': '📝',
      'json': '{}',
      'db': '🗄️',
      'sqlite': '🗄️'
    };
    return icons[ext] || '📄';
  }

  function toggleFolder(folderEl, folderName, folderChildren) {
    const isOpen = folderEl.classList.toggle('tree-folder--open');
    const arrow = folderName.querySelector('.tree-folder-arrow');

    if (isOpen) {
      arrow.textContent = '▼';
      folderChildren.style.display = 'block';
    } else {
      arrow.textContent = '▶';
      folderChildren.style.display = 'none';
    }
  }

  function handleFileClick(fileEl, filePath) {
    document.querySelectorAll('.tree-file').forEach(el => el.classList.remove('tree-file--active'));
    fileEl.classList.add('tree-file--active');
    previewFile(filePath);
  }

  async function previewFile(filePath) {
    try {
      const result = await window.API.readFile(currentProjectId, filePath);

      const preview = document.getElementById('explorer-preview');
      const filename = document.getElementById('explorer-preview-filename');
      const content = document.getElementById('explorer-preview-content');

      if (!preview || !filename || !content) return;

      const fileName = filePath.split(/[\/\\]/).pop();
      filename.textContent = fileName;

      const escaped = escapeHtml(result.content || '');
      content.textContent = escaped;

      preview.style.display = 'flex';
      content.scrollTop = 0;

    } catch (error) {
      console.error('Erreur preview fichier:', error);
      if (window.showToast) window.showToast('Erreur lecture fichier', 'error');
    }
  }

  function closePreview() {
    const preview = document.getElementById('explorer-preview');
    if (preview) {
      preview.style.display = 'none';
    }

    document.querySelectorAll('.tree-file').forEach(el => el.classList.remove('tree-file--active'));
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
})();
