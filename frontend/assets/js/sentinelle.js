(function () {
  let currentCycle = null;
  let pollInterval = null;

  document.addEventListener('DOMContentLoaded', async () => {
    await init();
    setupEventListeners();
  });

  async function init() {
    await loadBudget();
    await loadCycleActif();
    await loadPortefeuille();
    await loadWatchlist();
  }

  function setupEventListeners() {
    document.getElementById('toggle-portefeuille')?.addEventListener('click', () => togglePanel('portefeuille'));
    document.getElementById('toggle-watchlist')?.addEventListener('click', () => togglePanel('watchlist'));
    document.getElementById('btn-add-watchlist')?.addEventListener('click', handleAddWatchlist);
  }

  function togglePanel(panel) {
    const content = document.getElementById(`${panel}-content`);
    const icon = document.getElementById(`toggle-${panel}`)?.querySelector('.toggle-icon');
    if (content.style.display === 'none') {
      content.style.display = '';
      if (icon) icon.textContent = '▼';
    } else {
      content.style.display = 'none';
      if (icon) icon.textContent = '▶';
    }
  }

  async function loadBudget() {
    const now = new Date();
    const mois = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    try {
      const budget = await window.API.getBudgetMois(mois);
      document.getElementById('budget-display').innerHTML = `
        <div class="budget-item">
          <span class="text-muted">Budget ${mois}</span>
          <span class="budget-value">${budget.budget_restant.toFixed(2)}€</span>
        </div>
      `;
    } catch (e) {
      console.error('Erreur budget:', e);
    }
  }

  async function loadCycleActif() {
    try {
      const cycle = await window.API.getCycleActif();
      if (cycle) {
        currentCycle = cycle;
        renderCyclePhase(cycle);
      } else {
        renderInactif();
      }
    } catch (e) {
      renderInactif();
    }
  }

  function renderInactif() {
    const zone = document.getElementById('cycle-zone');
    zone.innerHTML = `
      <div class="card">
        <h2>Aucun cycle en cours</h2>
        <p class="text-muted">Lancez un nouveau cycle mensuel</p>
        <button id="btn-start-cycle" class="btn-primary">Lancer un cycle</button>
      </div>
    `;
    document.getElementById('btn-start-cycle').addEventListener('click', handleStartCycle);
  }

  async function handleStartCycle() {
    const now = new Date();
    const mois = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    try {
      const cycle = await window.API.createCycle({ mois, budget_mensuel: 20.0 });
      currentCycle = cycle;
      window.showToast('Cycle démarré', 'success');
      renderCyclePhase(cycle);
    } catch (e) {
      window.showToast('Erreur: ' + e.message, 'error');
    }
  }

  function renderCyclePhase(cycle) {
    const phase = cycle.etat;
    if (phase === 'PHASE_1') renderPhase1(cycle);
    else if (phase === 'PHASE_2') renderPhase2(cycle);
    else if (phase === 'PHASE_3') renderPhase3(cycle);
    else if (phase === 'PHASE_4') renderPhase4(cycle);
    else if (phase === 'PHASE_5') renderPhase5(cycle);
    else if (phase === 'PHASE_6') renderPhase6(cycle);
  }

  function renderPhase1(cycle) {
    const zone = document.getElementById('cycle-zone');
    zone.innerHTML = `
      <div class="card">
        <h2>Phase 1 — Saisie positions</h2>
        <p class="text-muted">Format: TICKER QUANTITE [PEA|CTO] / TICKER QUANTITE [PEA|CTO]</p>
        <p class="text-muted" style="font-size:0.85em">L'enveloppe est optionnelle (défaut PEA). Utilisez CTO pour les cryptos et actions étrangères hors EEA.</p>
        <input type="text" id="input-positions" placeholder="Ex: VWCE 5 PEA / BTC 0.001 CTO / IWDA 3" class="input-lg">
        <button id="btn-validate-positions" class="btn-primary">Valider les positions</button>
      </div>
    `;
    document.getElementById('btn-validate-positions').addEventListener('click', () => handleValidatePositions(cycle));
  }

  async function handleValidatePositions(cycle) {
    const input = document.getElementById('input-positions').value.trim();
    if (!input) return window.showToast('Saisissez au moins une position', 'warning');

    const enveloppes_valides = ['PEA', 'CTO', 'LIQUIDITES'];
    const parts = input.split('/').map(p => p.trim()).filter(p => p);
    for (const part of parts) {
      const tokens = part.split(/\s+/);
      const ticker = tokens[0];
      const quantite = tokens[1];
      if (!ticker || !quantite) continue;
      const enveloppe_raw = tokens[2] ? tokens[2].toUpperCase() : 'PEA';
      const enveloppe = enveloppes_valides.includes(enveloppe_raw) ? enveloppe_raw.toLowerCase() : 'PEA';
      try {
        await window.API.createPosition({
          ticker: ticker.toUpperCase(),
          quantite: parseFloat(quantite),
          enveloppe,
          date_entree: new Date().toISOString().split('T')[0]
        });
      } catch (e) {
        console.error('Erreur position:', e);
      }
    }
    
    await window.API.updateCycleEtat(cycle.id, { etat: 'PHASE_2' });
    window.showToast('Positions enregistrées, lancement veille...', 'info');
    await window.API.runVeille(cycle.id);
    await loadPortefeuille();
    await loadCycleActif();
    startPolling();
  }

  function renderPhase2(cycle) {
    const zone = document.getElementById('cycle-zone');
    if (!cycle.donnees_veille) {
      zone.innerHTML = `
        <div class="card">
          <h2>Phase 2 — Veille en cours</h2>
          <div class="spinner">Sentinelle scanne les marchés...</div>
        </div>
      `;
      startPolling();
    } else {
      const veille = JSON.parse(cycle.donnees_veille);
      zone.innerHTML = `
        <div class="card">
          <h2>Phase 2 — Veille terminée</h2>
          <div class="markdown-content">${window.renderMarkdown(veille.resume_ia)}</div>
          <button id="btn-continue-analyse" class="btn-primary">Continuer vers l'analyse</button>
        </div>
      `;
      document.getElementById('btn-continue-analyse').addEventListener('click', async () => {
        await window.API.updateCycleEtat(cycle.id, { etat: 'PHASE_3' });
        await window.API.runAnalyse(cycle.id);
        await loadCycleActif();
        startPolling();
      });
    }
  }

  function renderPhase3(cycle) {
    const zone = document.getElementById('cycle-zone');
    if (!cycle.donnees_analyse) {
      zone.innerHTML = `
        <div class="card">
          <h2>Phase 3 — Analyse en cours</h2>
          <div class="spinner">Sentinelle analyse votre portefeuille...</div>
        </div>
      `;
      startPolling();
    } else if (!cycle.donnees_propositions) {
      const analyse = JSON.parse(cycle.donnees_analyse);
      zone.innerHTML = `
        <div class="card">
          <h2>Phase 3 — Analyse terminée</h2>
          <div class="markdown-content">${window.renderMarkdown(analyse.resume_ia)}</div>
          <button id="btn-voir-propositions" class="btn-primary">Voir les propositions</button>
        </div>
      `;
      document.getElementById('btn-voir-propositions').addEventListener('click', async () => {
        await window.API.runPropositions(cycle.id);
        await loadCycleActif();
        startPolling();
      });
    } else {
      stopPolling();
      const propositions = JSON.parse(cycle.donnees_propositions);
      const biais = propositions.biais_detectes || [];
      let biaisHTML = '';
      if (biais.length > 0) {
        biaisHTML = '<div class="warning-box"><strong>⚠️ Biais détectés:</strong>';
        biais.forEach(b => {
          biaisHTML += `<p>${b.type}: ${b.details}</p>`;
        });
        biaisHTML += '</div>';
      }
      zone.innerHTML = `
        <div class="card">
          <h2>Phase 3 — Propositions</h2>
          <div class="markdown-content">${window.renderMarkdown(propositions.scenarios)}</div>
          ${biaisHTML}
          <button id="btn-valider-propositions" class="btn-primary">Valider</button>
        </div>
      `;
      document.getElementById('btn-valider-propositions').addEventListener('click', async () => {
        await window.API.updateCycleEtat(cycle.id, { etat: 'PHASE_4' });
        await loadCycleActif();
      });
    }
  }

  function renderPhase4(cycle) {
    const zone = document.getElementById('cycle-zone');
    const propositions = cycle.donnees_propositions ? JSON.parse(cycle.donnees_propositions) : null;
    const scenariosHTML = propositions
      ? `<div class="markdown-content" style="margin-bottom:1rem">${window.renderMarkdown(propositions.scenarios)}</div>`
      : '';

    zone.innerHTML = `
      <div class="card">
        <h2>Phase 4 — Décision</h2>
        ${scenariosHTML}
        <p class="text-muted">Nommez le scénario choisi (ex: "Scénario 1 — VWCE") ou passez en accumulation</p>
        <input type="text" id="input-scenario" placeholder="Nom du scénario choisi" class="input-lg">
        <div class="scenario-choice" style="display:flex;gap:0.75rem;margin-top:0.75rem">
          <button id="btn-valider-scenario" class="btn-primary">Valider ce scénario → Ordre</button>
          <button id="btn-accumulation" class="btn-secondary">Accumulation (aucun achat)</button>
        </div>
      </div>
    `;

    document.getElementById('btn-valider-scenario').addEventListener('click', async () => {
      const scenario = document.getElementById('input-scenario').value.trim();
      if (!scenario) return window.showToast('Nommez le scénario choisi', 'warning');
      await window.API.updateCycleDecision(cycle.id, { mode: 'normal', decision: scenario });
      await window.API.updateCycleEtat(cycle.id, { etat: 'PHASE_5' });
      const montant = propositions ? propositions.budget_disponible : 20.0;
      await window.API.runOrdre(cycle.id, { scenario_choisi: scenario, montant });
      await loadCycleActif();
    });

    document.getElementById('btn-accumulation').addEventListener('click', async () => {
      await window.API.updateCycleDecision(cycle.id, { mode: 'accumulation', decision: 'Accumulation' });
      await window.API.updateCycleEtat(cycle.id, { etat: 'PHASE_6' });
      await loadCycleActif();
    });
  }

  function renderPhase5(cycle) {
    const zone = document.getElementById('cycle-zone');
    
    // Extraire le ticker du scénario choisi si possible
    let tickerExtrait = '';
    if (cycle.decision) {
      const match = cycle.decision.match(/\b([A-Z]{2,5})\b/);
      if (match) tickerExtrait = match[1];
    }
    
    // Afficher les paramètres d'ordre si disponibles
    let ordreInfo = '';
    try {
      const propositions = cycle.donnees_propositions ? JSON.parse(cycle.donnees_propositions) : null;
      if (propositions && propositions.ordre) {
        ordreInfo = `
          <div style="background:var(--bg-secondary);padding:1rem;border-radius:6px;margin-bottom:1rem">
            <strong>Paramètres d'ordre suggérés :</strong>
            <pre style="margin:0.5rem 0 0;font-size:0.9rem;white-space:pre-wrap">${JSON.stringify(propositions.ordre, null, 2)}</pre>
          </div>
        `;
      }
    } catch (e) {}
    
    const today = new Date().toISOString().split('T')[0];
    
    zone.innerHTML = `
      <div class="card">
        <h2>Phase 5 — Confirmation de l'achat réel</h2>
        <p class="text-muted">Scénario choisi : <strong>${cycle.decision || 'N/A'}</strong></p>
        ${ordreInfo}
        
        <form id="form-confirm-achat" style="display:flex;flex-direction:column;gap:1rem;margin-top:1.5rem">
          <div>
            <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Ticker *</label>
            <input type="text" id="input-ticker" value="${tickerExtrait}" required style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
          </div>
          
          <div>
            <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Quantité réelle achetée *</label>
            <input type="number" id="input-quantite" step="0.01" required style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
          </div>
          
          <div>
            <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Prix unitaire réel payé (€) *</label>
            <input type="number" id="input-prix" step="0.01" required style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
          </div>
          
          <div>
            <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Frais (€)</label>
            <input type="number" id="input-frais" value="1.0" step="0.01" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
          </div>
          
          <div>
            <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Date de transaction *</label>
            <input type="date" id="input-date-transaction" value="${today}" required style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
          </div>
          
          <div>
            <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Enveloppe *</label>
            <select id="input-enveloppe" required style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
              <option value="PEA">PEA</option>
              <option value="CTO">CTO</option>
            </select>
          </div>
          
          <button type="submit" class="btn-primary">Confirmer l'achat</button>
        </form>
      </div>
    `;
    
    document.getElementById('form-confirm-achat').addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const ticker = document.getElementById('input-ticker').value.trim();
      const quantite = parseFloat(document.getElementById('input-quantite').value);
      const prix = parseFloat(document.getElementById('input-prix').value);
      const frais = parseFloat(document.getElementById('input-frais').value) || 0.0;
      const dateTransaction = document.getElementById('input-date-transaction').value;
      const enveloppe = document.getElementById('input-enveloppe').value;
      
      if (!ticker || !quantite || !prix || !dateTransaction || !enveloppe) {
        return window.showToast('Tous les champs requis doivent être remplis', 'error');
      }
      
      try {
        // Créer la transaction
        await window.API.createTransaction({
          cycle_id: cycle.id,
          ticker,
          quantite,
          prix_reel: prix,
          frais,
          date_transaction: dateTransaction
        });
        
        // Upsert la position
        await window.API.upsertPosition({
          ticker,
          quantite,
          prix_unitaire: prix,
          enveloppe,
          date_entree: dateTransaction
        });
        
        // Passer à Phase 6
        await window.API.updateCycleEtat(cycle.id, { etat: 'PHASE_6' });
        
        window.showToast('Achat confirmé et position mise à jour', 'success');
        await loadCycleActif();
      } catch (error) {
        window.showToast('Erreur : ' + error.message, 'error');
      }
    });
  }

  function renderPhase6(cycle) {
    const zone = document.getElementById('cycle-zone');
    zone.innerHTML = `
      <div class="card">
        <h2>Phase 6 — Clôture</h2>
        <p class="text-muted">Cycle terminé</p>
        <button id="btn-cloturer" class="btn-primary">Clôturer</button>
      </div>
    `;
    document.getElementById('btn-cloturer').addEventListener('click', async () => {
      await window.API.cloturerCycle(cycle.id, {});
      window.showToast('Cycle clôturé', 'success');
      currentCycle = null;
      stopPolling();
      await loadCycleActif();
    });
  }

  function startPolling() {
    stopPolling();
    pollInterval = setInterval(async () => {
      await loadCycleActif();
    }, 3000);
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  }

  async function loadPortefeuille() {
    try {
      const data = await window.API.getPositionsValorisation();
      const list = document.getElementById('portefeuille-list');
      
      if (!data.positions || data.positions.length === 0) {
        list.innerHTML = '<p class="text-muted">Aucune position</p>';
        return;
      }
      
      const positionsHTML = data.positions.map(p => {
        const coursHTML = p.cours_actuel !== null ? `${p.cours_actuel.toFixed(2)} €` : 'N/A';
        const valorisationHTML = p.valorisation_actuelle !== null ? `${p.valorisation_actuelle.toFixed(2)} €` : 'N/A';
        
        let pvHTML = '';
        if (p.plus_value_latente !== null && p.plus_value_pct !== null) {
          const pvClass = p.plus_value_latente >= 0 ? 'text-success' : 'text-danger';
          const pvSign = p.plus_value_latente >= 0 ? '+' : '';
          pvHTML = `<div class="${pvClass}" style="font-size:0.85rem">${pvSign}${p.plus_value_latente.toFixed(2)} € (${pvSign}${p.plus_value_pct.toFixed(2)}%)</div>`;
        }
        
        return `
          <div class="position-item" style="padding:0.75rem;border-bottom:1px solid var(--border)">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.25rem">
              <strong>${p.ticker}</strong>
              <span class="text-muted">${p.enveloppe}</span>
            </div>
            <div style="font-size:0.85rem;color:var(--text-muted)">
              Qté: ${p.quantite} | Cours: ${coursHTML}
            </div>
            <div style="font-size:0.85rem;color:var(--text-muted)">
              Valorisation: ${valorisationHTML}
            </div>
            ${pvHTML}
          </div>
        `;
      }).join('');
      
      const totalHTML = `
        <div style="padding:1rem;background:var(--bg-secondary);border-radius:6px;margin-top:0.5rem">
          <div style="font-weight:bold;margin-bottom:0.5rem">Total portefeuille</div>
          <div style="font-size:0.9rem">Valorisation: ${data.total_valorisation.toFixed(2)} €</div>
          <div style="font-size:0.9rem">Prix de revient: ${data.total_prix_revient.toFixed(2)} €</div>
          <div style="font-size:0.9rem" class="${data.total_plus_value >= 0 ? 'text-success' : 'text-danger'}">
            ${data.total_plus_value >= 0 ? '+' : ''}${data.total_plus_value.toFixed(2)} € (${data.total_plus_value >= 0 ? '+' : ''}${data.total_plus_value_pct.toFixed(2)}%)
          </div>
        </div>
      `;
      
      list.innerHTML = positionsHTML + totalHTML;
    } catch (e) {
      console.error('Erreur portefeuille:', e);
      document.getElementById('portefeuille-list').innerHTML = '<p class="text-danger">Erreur chargement</p>';
    }
  }

  async function loadWatchlist() {
    try {
      const watchlist = await window.API.getWatchlist();
      const list = document.getElementById('watchlist-list');
      if (watchlist.length === 0) {
        list.innerHTML = '<p class="text-muted">Aucun actif surveillé</p>';
        return;
      }
      list.innerHTML = watchlist.map(w => `
        <div class="watchlist-item">
          <div><strong>${w.ticker}</strong> <span class="badge badge-${w.niveau_risque}">${w.niveau_risque}</span></div>
          <button class="btn-sm btn-danger" onclick="handleDeleteWatchlist(${w.id})">×</button>
        </div>
      `).join('');
    } catch (e) {
      console.error('Erreur watchlist:', e);
    }
  }

  async function handleAddWatchlist() {
    const ticker = document.getElementById('watchlist-ticker').value.trim().toUpperCase();
    const niveau_risque = document.getElementById('watchlist-risque').value;
    if (!ticker) return window.showToast('Saisissez un ticker', 'warning');
    try {
      await window.API.createWatchlist({ ticker, niveau_risque });
      window.showToast('Actif ajouté', 'success');
      document.getElementById('watchlist-ticker').value = '';
      await loadWatchlist();
    } catch (e) {
      window.showToast('Erreur: ' + e.message, 'error');
    }
  }

  window.handleDeleteWatchlist = async function(id) {
    try {
      await window.API.deleteWatchlist(id);
      window.showToast('Actif retiré', 'success');
      await loadWatchlist();
    } catch (e) {
      window.showToast('Erreur: ' + e.message, 'error');
    }
  };
})();
