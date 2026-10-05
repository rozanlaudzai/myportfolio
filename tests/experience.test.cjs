// Run with: node --test tests/experience.test.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const script = readFileSync(new URL('../static/js/experience.js', `file://${__filename}`), 'utf8');

function setup(role = 'visitor') {
  const elements = new Map();
  function element() {
    return {
      dataset: {}, value: '', hidden: true, children: [], handlers: {},
      setAttribute() {},
      classList: { toggle(name, hidden) { this.hidden = hidden; } },
      addEventListener(name, handler) { this.handlers[name] = handler; },
      replaceChildren(...children) { this.children = children; },
    };
  }
  for (const id of ['page', 'search-form', 'search-input', 'list', 'loading', 'empty', 'error']) {
    elements.set(`experience-${id}`, element());
  }
  const get = (name) => elements.get(`experience-${name}`);
  get('page').dataset = {
    endpoint: '/api/experience', isSuperuser: String(role === 'owner'),
    isEditor: String(role === 'editor'),
    editUrl: '/experience/00000000-0000-0000-0000-000000000000/edit/',
    deleteUrl: '/experience/00000000-0000-0000-0000-000000000000/delete/',
  };
  const requests = [];
  const timers = new Map();
  let timerId = 0;
  vm.runInNewContext(script, {
    document: { getElementById: (id) => elements.get(id), createElement: element },
    window: { location: { origin: 'https://example.com', href: 'https://example.com/experience/' } },
    URL, AbortController,
    setTimeout(callback, delay) { timers.set(++timerId, { callback, delay }); return timerId; },
    clearTimeout(id) { timers.delete(id); },
    fetch(url, options) {
      return new Promise((resolve, reject) => requests.push({ url, options, resolve, reject }));
    },
  });
  return { get, requests, timers };
}
const item = {
  pk: '123', fields: {
    title: '<img src=x onerror=alert(1)>', company_name: 'A & B',
    company_logo: 'javascript:alert(1)', description: 'First\n<b>Second</b>',
    started_at: '2026-01-01', ended_at: null, skill_names: ['<script>bad</script>'],
  },
};
async function respond(request, data, ok = true) {
  request.resolve({ ok, json: async () => data });
  await new Promise(setImmediate);
}

test('renders escaped text, line breaks, dates, skills and role-specific actions', async () => {
  for (const role of ['visitor', 'editor', 'owner']) {
    const { get, requests } = setup(role);
    await respond(requests[0], [item]);
    const html = get('list').children[0].innerHTML;
    assert.match(html, /&lt;img/);
    assert.match(html, /First<br>&lt;b&gt;Second&lt;\/b&gt;/);
    assert.match(html, /&lt;script&gt;bad/);
    assert.match(html, /Jan 2026/);
    assert.match(html, /<time>Present<\/time>/);
    assert.doesNotMatch(html, /<img|javascript:/);
    assert.equal(html.includes('/123/edit/'), role !== 'visitor');
    assert.equal(html.includes('/123/delete/'), role === 'owner');
    assert.equal(get('list').classList.hidden, false);
  }
});

test('renders safe logos and completed dates', async () => {
  const { get, requests } = setup();
  await respond(requests[0], [{ ...item, fields: {
    ...item.fields, company_logo: 'https://example.com/logo.png', ended_at: '2026-09-30', skill_names: [],
  } }]);
  const html = get('list').children[0].innerHTML;
  assert.match(html, /src="https:\/\/example.com\/logo.png"/);
  assert.match(html, /Sep 2026/);
  assert.doesNotMatch(html, /Present/);
});

test('debounces typing for 300 ms and submits immediately without a duplicate request', () => {
  const { get, requests, timers } = setup();
  get('search-input').value = ' dev ';
  get('search-input').handlers.input();
  get('search-input').handlers.input();
  assert.equal(timers.size, 1);
  assert.equal([...timers.values()][0].delay, 300);
  assert.equal(requests.length, 1);
  [...timers.values()][0].callback();
  assert.equal(requests.length, 2);
  assert.equal(requests[1].url.searchParams.get('title'), 'dev');
  get('search-input').handlers.input();
  let prevented = false;
  get('search-form').handlers.submit({ preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(timers.size, 0);
  assert.equal(requests.length, 3);
});

test('stale responses cannot replace newer results, even during the debounce delay', async () => {
  const { get, requests } = setup();
  get('search-input').value = 'new';
  get('search-input').handlers.input();
  assert.equal(requests[0].options.signal.aborted, true);
  await respond(requests[0], [item]);
  assert.equal(get('list').children.length, 0);
  get('search-form').handlers.submit({ preventDefault() {} });
  await respond(requests[1], []);
  assert.equal(get('empty').textContent, 'No experiences found.');
  assert.equal(get('empty').classList.hidden, false);
});

test('handles empty data, HTTP failures, network failures, and recovery', async () => {
  const { get, requests } = setup();
  const submit = () => get('search-form').handlers.submit({ preventDefault() {} });
  await respond(requests[0], []);
  assert.equal(get('empty').textContent, 'No experience added yet.');
  submit();
  await respond(requests[1], null, false);
  assert.equal(get('error').classList.hidden, false);
  submit();
  requests[2].reject(new Error('offline'));
  await new Promise(setImmediate);
  assert.equal(get('error').classList.hidden, false);
  submit();
  await respond(requests[3], [item]);
  assert.equal(get('list').classList.hidden, false);
  assert.equal(get('error').classList.hidden, true);
});
