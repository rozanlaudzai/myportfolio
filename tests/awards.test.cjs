// Run with: node --test tests/awards.test.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const template = readFileSync(new URL('../main/templates/main/awards.html', `file://${__filename}`), 'utf8');

function setup(role = 'visitor') {
  function element() {
    return { value: '', dataset: {}, children: [], handlers: {},
      classList: { toggle(name, hidden) { this.hidden = hidden; } },
      addEventListener(name, handler) { this.handlers[name] = handler; },
      replaceChildren(...items) { this.children = items; },
    };
  }
  const elements = Object.fromEntries(['loading', 'error', 'empty', 'list', 'award-search-form', 'search-input'].map(id => [id, element()]));
  const requests = [], timers = new Map(), toasts = [];
  let timer = 0;
  const script = template.match(/<script>([\s\S]*?)<\/script>/)[1]
    .replace(/{{ user.is_superuser\|yesno:'true,false' }}/g, String(role === 'owner'))
    .replace(/{{ is_editor\|yesno:'true,false' }}/g, String(role === 'editor'))
    .replace(/{{ user.is_authenticated\|yesno:'true,false' }}/g, String(role !== 'guest'))
    .replace(/{% url '([^']+)'(?: '([^']+)')? %}/g, (_, name, id) => ({
      'api:award-list': '/api/v1/awards/',
      'api:award-detail': `/api/v1/awards/${id}/`,
      'api:award-star': `/api/v1/awards/${id}/star/`,
      'main:edit_award': `/awards/${id}/edit/`,
      'main:login': '/login/', 'main:show_awards': '/awards/',
    })[name]);
  const context = vm.createContext({
    document: { cookie: 'csrftoken=test-token', getElementById: id => elements[id], createElement: element },
    window: { location: { origin: 'https://example.com' } }, URL, AbortController,
    showToast: (...args) => toasts.push(args),
    setTimeout(fn, delay) { timers.set(++timer, { fn, delay }); return timer; },
    clearTimeout(id) { timers.delete(id); },
    fetch(url, options) { return new Promise((resolve, reject) => requests.push({ url, options, resolve, reject })); },
  });
  vm.runInContext(script, context);
  return { elements, requests, timers, toasts, context };
}
const award = { id: '123', title: '<img src=x onerror=alert(1)>', issuer: 'A & B',
  description: 'First\n<b>Second</b>', awarded_at: '2026-10-01', star_count: 1,
  is_starred: false, starred_by_names: '<script>bad</script>' };
async function respond(request, data, status = 200) {
  request.resolve({ ok: status < 400, status, json: async () => data });
  await new Promise(setImmediate);
}

test('uses flat DRF data, escapes text and preserves role-specific actions', async () => {
  for (const role of ['guest', 'visitor', 'editor', 'owner']) {
    const { elements, requests } = setup(role);
    assert.equal(requests[0].url.pathname, '/api/v1/awards/');
    assert.equal(requests[0].options.headers.Accept, 'application/json');
    await respond(requests[0], [award]);
    const html = elements.list.children[0].innerHTML;
    assert.match(html, /&lt;img/);
    assert.match(html, /First<br>&lt;b&gt;Second&lt;\/b&gt;/);
    assert.match(html, /&lt;script&gt;bad/);
    assert.match(html, /Oct 2026/);
    assert.doesNotMatch(html, /<img|<script/);
    assert.equal(html.includes('/123/edit/'), ['owner', 'editor'].includes(role));
    assert.equal(html.includes('data-action="delete"'), role === 'owner');
    assert.equal(html.includes('data-action="star"'), role !== 'guest');
    assert.equal(html.includes('/login/?next=/awards/'), role === 'guest');
  }
});

test('debounces search and ignores stale results during debounce', async () => {
  const { elements, requests, timers } = setup();
  elements['search-input'].value = ' new ';
  elements['search-input'].handlers.input();
  elements['search-input'].handlers.input();
  assert.equal(timers.size, 1);
  assert.equal([...timers.values()][0].delay, 300);
  assert.equal(requests[0].options.signal.aborted, true);
  await respond(requests[0], [award]);
  assert.equal(elements.list.children.length, 0);
  elements['award-search-form'].handlers.submit({ preventDefault() {} });
  assert.equal(timers.size, 0);
  assert.equal(requests[1].url.searchParams.get('title'), 'new');
  await respond(requests[1], []);
  assert.equal(elements.empty.classList.hidden, false);
});

test('writes JSON with CSRF and handles 204, field errors and HTML errors', async () => {
  const { context, requests } = setup();
  const deleted = vm.runInContext('writeAward("/api/v1/awards/123/", "DELETE")', context);
  requests[1].resolve({ status: 204, json() { throw new Error('204 must not parse JSON'); } });
  assert.equal(await deleted, null);
  const created = vm.runInContext('writeAward("/api/v1/awards/", "POST", {title: "New"})', context);
  assert.equal(requests[2].options.headers['X-CSRFToken'], 'test-token');
  assert.equal(requests[2].options.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(requests[2].options.body), { title: 'New' });
  const invalid = assert.rejects(created, /title: Required/);
  await respond(requests[2], { title: ['Required'] }, 400);
  await invalid;
  const failed = vm.runInContext('writeAward("/api/v1/awards/", "POST", {})', context);
  const rejected = assert.rejects(failed, /HTTP 502/);
  requests[3].resolve({ status: 502, ok: false, json: async () => { throw new Error('HTML'); } });
  await rejected;
});

test('delegated delete stays on page, disables button and refreshes active search', async () => {
  const { elements, requests, toasts } = setup('owner');
  elements['search-input'].value = ' current ';
  let hidden = false;
  const button = { disabled: false, dataset: { action: 'delete', id: '123' },
    closest() { return { hidePopover() { hidden = true; } }; } };
  const operation = elements.list.handlers.click({ target: { closest: () => button } });
  assert.equal(button.disabled, true);
  assert.equal(requests[1].options.method, 'DELETE');
  assert.equal(requests[1].url, '/api/v1/awards/123/');
  await respond(requests[1], null, 204);
  assert.equal(hidden, true);
  assert.equal(requests[2].url.searchParams.get('title'), 'current');
  await respond(requests[2], []);
  await operation;
  assert.equal(button.disabled, false);
  assert.equal(toasts[0][2], 'success');
});
