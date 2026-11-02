const statusEl = document.getElementById('last-check');
const titleEl = document.getElementById('status-title');
const detailEl = document.getElementById('status-detail');
const itemsEl = document.getElementById('items');
const countEl = document.getElementById('item-count');
const dotEl = document.getElementById('status-dot');

function safeDate(value) {
  if (!value) return 'Non disponibile';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? 'Non disponibile' : d.toLocaleString('it-IT', { dateStyle:'medium', timeStyle:'short' });
}
function renderItems(items) {
  itemsEl.replaceChildren();
  const valid = Array.isArray(items) ? items : [];
  countEl.textContent = String(valid.length);
  if (!valid.length) {
    const p = document.createElement('p');
    p.className = 'empty';
    p.textContent = 'Nessun collegamento pertinente trovato nello stato attuale. Consulta la pagina ufficiale.';
    itemsEl.append(p);
    return;
  }
  valid.forEach(item => {
    if (!item || !item.url) return;
    const a = document.createElement('a');
    a.className = 'item';
    a.href = item.url;
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = item.title || item.url;
    const small = document.createElement('small');
    small.textContent = item.url;
    a.append(small);
    itemsEl.append(a);
  });
}
async function loadStatus() {
  titleEl.textContent = 'Monitoraggio automatico';
  statusEl.textContent = 'Aggiornamento in corso…';
  detailEl.textContent = 'Recupero dell’ultimo controllo effettuato da GitHub.';
  try {
    const response = await fetch('./status.json?ts=' + Date.now(), { cache:'no-store' });
    if (!response.ok) throw new Error('status non disponibile');
    const s = await response.json();
    statusEl.textContent = 'Ultimo controllo: ' + safeDate(s.checked_at);
    if (s.last_change) {
      detailEl.textContent = 'Ultima variazione rilevata: ' + s.last_change + '. Apri la pagina UniFG per verificarla.';
      dotEl.classList.add('warn');
    } else {
      detailEl.textContent = 'Nessuna variazione registrata dopo il controllo iniziale. Il controllo viene ripetuto ogni 6 ore circa.';
      dotEl.classList.remove('warn');
    }
    renderItems(s.items);
  } catch (e) {
    titleEl.textContent = 'Stato non ancora disponibile';
    statusEl.textContent = 'Non riesco a leggere l’ultimo controllo.';
    detailEl.textContent = 'Verifica che GitHub Actions abbia completato almeno un’esecuzione e riprova.';
    itemsEl.innerHTML = '<p class="empty">I collegamenti saranno mostrati dopo un controllo riuscito.</p>';
    countEl.textContent = '—';
  }
}
document.getElementById('refresh').addEventListener('click', loadStatus);
loadStatus();
