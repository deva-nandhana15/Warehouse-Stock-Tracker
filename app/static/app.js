'use strict';
const $ = (selector) => document.querySelector(selector);
let items = [];
let view = 'all';
let mode = 'add';
let selected = null;
let toastTimer;
let loading = false;
let submitting = false;
const formatter = new Intl.NumberFormat();
const dialog = $('#item-dialog');
const form = $('#item-form');

function icon(name) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  const use = document.createElementNS(svg.namespaceURI, 'use');
  use.setAttribute('href', `#${name}`);
  svg.setAttribute('aria-hidden', 'true');
  svg.append(use);
  return svg;
}
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function notify(message) {
  clearTimeout(toastTimer);
  $('#toast').textContent = message;
  $('#toast').hidden = false;
  toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 4500);
}
async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } });
  let data;
  try { data = await response.json(); } catch { throw new Error('The server returned an unexpected response. Please try again.'); }
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}
function render() {
  const low = items.filter(item => item.quantity <= item.reorder_level);
  $('#total-items').textContent = formatter.format(items.length);
  $('#total-units').textContent = formatter.format(items.reduce((sum, item) => sum + item.quantity, 0));
  $('#low-count').textContent = formatter.format(low.length);
  $('#nav-total').textContent = items.length;
  $('#nav-low').textContent = low.length;
  const query = $('#search').value.trim().toLowerCase();
  const filtered = (view === 'low' ? low : items).filter(item => `${item.name} ${item.sku}`.toLowerCase().includes(query));
  $('#item-count').textContent = filtered.length;
  $('#results-count').textContent = `${filtered.length} of ${items.length} item${items.length === 1 ? '' : 's'}`;
  const body = $('#inventory-body');
  body.replaceChildren();
  if (!filtered.length) {
    const row = element('tr');
    const cell = element('td', 'empty', query ? 'No matching items. Try another search.' : view === 'low' ? 'All stocked up. No low-stock items.' : 'A fresh start. Add your first item.');
    cell.colSpan = 6;
    row.append(cell); body.append(row);
  }
  for (const item of filtered) {
    const row = element('tr');
    const nameCell = element('td');
    const name = element('div', 'item-cell');
    const mark = element('span', 'item-icon'); mark.append(icon('box'));
    name.append(mark, element('span', 'item-name', item.name)); nameCell.append(name);
    const isLow = item.quantity <= item.reorder_level;
    const status = element('td');
    status.append(element('span', `badge${isLow ? ' low' : ''}`, item.quantity === 0 ? 'Out of stock' : isLow ? 'Low stock' : 'In stock'));
    const actions = element('td');
    const group = element('div', 'row-actions');
    for (const action of ['receive', 'issue']) {
      const button = element('button', action);
      button.type = 'button';
      const label = action === 'receive' ? 'Receive' : 'Issue';
      button.setAttribute('aria-label', `${label} stock for ${item.name}`);
      button.title = `${label} stock`;
      button.append(icon('arrow'), document.createTextNode(label));
      button.addEventListener('click', () => openDialog(action, item));
      group.append(button);
    }
    actions.append(group);
    row.append(nameCell, element('td', 'sku', item.sku), element('td', 'number stock-number', formatter.format(item.quantity)), element('td', 'number', formatter.format(item.reorder_level)), status, actions);
    body.append(row);
  }
}
async function refresh() {
  if (loading) return;
  loading = true; $('#refresh').disabled = true;
  $('#inventory-body').setAttribute('aria-busy', 'true');
  try {
    items = await api('/items');
    $('#load-error').hidden = true;
    render();
  } catch (error) {
    $('#load-error').textContent = `${error.message} Use refresh to reconnect.`;
    $('#load-error').hidden = false;
    $('#results-count').textContent = 'Unable to sync inventory';
    if (!items.length) {
      const row = element('tr'); const cell = element('td', 'empty', 'Inventory unavailable. Refresh to try again.');
      cell.colSpan = 6; row.append(cell); $('#inventory-body').replaceChildren(row);
    }
  } finally {
    loading = false; $('#refresh').disabled = false;
    $('#inventory-body').setAttribute('aria-busy', 'false');
  }
}
function setView(next) {
  view = next;
  document.querySelectorAll('[data-view]').forEach(button => {
    const active = button.dataset.view === view;
    if (button.classList.contains('nav-item')) {
      button.classList.toggle('active', active);
      if (active) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
    } else {
      button.classList.toggle('selected', active);
      button.setAttribute('aria-pressed', String(active));
    }
  });
  $('#page-title').textContent = $('#breadcrumb').textContent = view === 'low' ? 'Low stock' : 'Inventory';
  $('#page-subtitle').textContent = view === 'low' ? 'A little attention goes a long way.' : 'A little clarity for everything you keep.';
  $('#table-heading').firstChild.textContent = view === 'low' ? 'Needs attention ' : 'All inventory ';
  $('#table-description').textContent = view === 'low' ? 'Items at or below their reorder level.' : 'The right stock. In the right place.';
  render();
}
function openDialog(nextMode, item = null) {
  mode = nextMode; selected = item; form.reset();
  const adding = mode === 'add';
  $('#add-fields').hidden = !adding; $('#reorder-field').hidden = !adding;
  for (const name of ['name', 'sku', 'reorder_level']) form.elements[name].disabled = !adding;
  $('#form-error').hidden = true;
  form.elements.quantity.min = adding ? '0' : '1';
  form.elements.quantity.value = adding ? '0' : '1';
  const title = adding ? 'Add an item' : mode === 'receive' ? 'Receive stock' : 'Issue stock';
  $('#dialog-title').textContent = title;
  $('#save-item').textContent = title;
  $('#dialog-eyebrow').textContent = adding ? 'MAKE ROOM FOR SOMETHING NEW' : 'A SMALL ADJUSTMENT';
  $('#dialog-description').textContent = adding ? "A few details, and you're ready to go." : `${item.name} · ${item.sku} · ${formatter.format(item.quantity)} on hand`;
  $('#quantity-label').textContent = adding ? 'Opening quantity' : 'Quantity';
  dialog.showModal();
  (adding ? $('#item-name') : form.elements.quantity).focus();
}
function closeDialog() { if (!submitting) dialog.close(); }
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (submitting) return;
  const quantity = Number(form.elements.quantity.value);
  const adding = mode === 'add';
  const payload = { quantity };
  if (adding) Object.assign(payload, { name: form.elements.name.value.trim(), sku: form.elements.sku.value, reorder_level: Number(form.elements.reorder_level.value) });
  const numbers = adding ? [quantity, payload.reorder_level] : [quantity];
  if (!numbers.every(Number.isSafeInteger) || quantity < (adding ? 0 : 1) || (adding && payload.reorder_level < 0)) {
    $('#form-error').textContent = 'Enter valid whole numbers within the supported range.';
    $('#form-error').hidden = false; return;
  }
  submitting = true;
  $('#save-item').disabled = true; $('#cancel-dialog').disabled = true; $('#close-dialog').disabled = true;
  $('#form-error').hidden = true;
  try {
    const path = adding ? '/items' : `/items/${encodeURIComponent(selected.sku)}/${mode}`;
    await api(path, { method: 'POST', body: JSON.stringify(payload) });
    dialog.close();
    notify(adding ? 'Item added to your inventory.' : mode === 'receive' ? 'Stock received. All set.' : 'Stock issued. Inventory updated.');
    await refresh();
  } catch (error) { $('#form-error').textContent = error.message; $('#form-error').hidden = false; }
  finally { submitting = false; $('#save-item').disabled = false; $('#cancel-dialog').disabled = false; $('#close-dialog').disabled = false; }
});
dialog.addEventListener('cancel', event => { if (submitting) event.preventDefault(); });
$('#close-dialog').addEventListener('click', closeDialog);
$('#cancel-dialog').addEventListener('click', closeDialog);
$('#add-item').addEventListener('click', () => openDialog('add'));
$('#refresh').addEventListener('click', refresh);
$('#search').addEventListener('input', render);
$('#low-stock-card').addEventListener('click', () => setView('low'));
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
async function loadStorageInfo() {
  try {
    const info = await api('/storage');
    $('#storage-label').textContent = info.persistent ? 'Azure Table Storage' : 'In-memory inventory';
    $('#storage-note').textContent = info.persistent ? 'Inventory is saved in Azure.' : 'Inventory resets when the server restarts.';
  } catch {
    $('#storage-label').textContent = 'Storage status unavailable';
    $('#storage-note').textContent = 'Unable to check storage configuration.';
  }
}
loadStorageInfo();
refresh();
