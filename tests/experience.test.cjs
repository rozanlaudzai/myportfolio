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
      showPopover() { this.open = true; }, hidePopover() { this.open = false; },
      querySelector() { return this.submitButton; }, reset() { this.wasReset = true; },
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
    endpoint: '/api/v1/experiences/', isSuperuser: String(role === 'owner'),
    isEditor: String(role === 'editor'), isAuthenticated: String(role !== 'visitor'),
    starUrl: '/api/v1/experiences/00000000-0000-0000-0000-000000000000/star/',
    editUrl: '/experience/00000000-0000-0000-0000-000000000000/edit/',
    deleteUrl: '/experience/00000000-0000-0000-0000-000000000000/delete/',
  };
  const form = element();
  form.submitButton = { disabled: false };
  form.elements = Object.fromEntries(['title', 'company_name', 'company_logo', 'description', 'started_at', 'ended_at', 'skills'].map(name => [name, { value: '' }]));
  if (role === 'owner' || role === 'editor') elements.set('experience-form', form);
  const modal = element();
  elements.set('add-experience-modal', modal);
  const toasts = [];
  const requests = [];
  const timers = new Map();
  let timerId = 0;
  vm.runInNewContext(script, {
    showToast: (...args) => toasts.push(args),
    document: { cookie: 'csrftoken=test-token', getElementById: (id) => elements.get(id), createElement: element },
    window: { location: { origin: 'https://example.com', href: 'https://example.com/experience/' } },
    URL, AbortController,
    setTimeout(callback, delay) { timers.set(++timerId, { callback, delay }); return timerId; },
    clearTimeout(id) { timers.delete(id); },
    fetch(url, options) {
      return new Promise((resolve, reject) => requests.push({ url, options, resolve, reject }));
    },
  });
  return { get, requests, timers, form, modal, toasts };
}
const item = {
  id: '123',
    title: '<img src=x onerror=alert(1)>', company_name: 'A & B',
    company_logo: 'javascript:alert(1)', description: 'First\n<b>Second</b>',
    started_at: '2026-01-01', ended_at: null, skills: ['<script>bad</script>'],
  star_count: 0, is_starred: false,
};
async function respond(request, data, ok = true, status = 200) {
  request.resolve({ ok, status, json: async () => data });
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
    assert.equal(html.includes('data-action="edit"'), role !== 'visitor');
    assert.equal(html.includes('data-action="delete"'), role === 'owner');
    assert.equal(get('list').classList.hidden, false);
  }
});

test('renders safe logos and completed dates', async () => {
  const { get, requests } = setup();
  await respond(requests[0], [{ ...item, company_logo: 'https://example.com/logo.png', ended_at: '2026-09-30', skills: [],
  }]);
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

function clickAction(get, action, id = '123') {
  const button = { dataset: { action, id }, disabled: false, closest() { return null; } };
  get('list').handlers.click({ target: { closest: () => button } });
  return button;
}

test('edit prefills the modal and sends PATCH JSON with CSRF; errors preserve input', async () => {
  const { get, requests, form, modal, toasts } = setup('editor');
  await respond(requests[0], [item]);
  clickAction(get, 'edit');
  assert.equal(modal.open, true);
  assert.equal(form.elements.title.value, item.title);
  assert.equal(form.elements.skills.value, item.skills.join(', '));
  form.elements.title.value = 'Edited';
  const submit = () => form.handlers.submit({ preventDefault() {} });
  submit();
  assert.equal(requests[1].options.method, 'PATCH');
  assert.equal(requests[1].options.headers['X-CSRFToken'], 'test-token');
  assert.equal(JSON.parse(requests[1].options.body).title, 'Edited');
  assert.equal(JSON.parse(requests[1].options.body).ended_at, null);
  await respond(requests[1], { title: ['Invalid title'] }, false, 400);
  assert.match(toasts.at(-1)[1], /title: Invalid title/);
  assert.equal(form.elements.title.value, 'Edited');
  assert.equal(modal.open, true);
  submit();
  await respond(requests[2], { detail: 'Forbidden' }, false, 403);
  assert.match(toasts.at(-1)[1], /Forbidden/);
  submit();
  await respond(requests[3], item);
  assert.equal(modal.open, false);
  assert.equal(form.wasReset, true);
  assert.equal(requests.length, 5);
  await respond(requests[4], [item]);
});

test('owner creates JSON and star/delete use API with CSRF and handle 204', async () => {
  const { get, requests, form } = setup('owner');
  await respond(requests[0], [item]);
  form.elements.skills.value = 'Python, Django';
  form.handlers.submit({ preventDefault() {} });
  assert.equal(requests[1].options.method, 'POST');
  assert.deepEqual(JSON.parse(requests[1].options.body).skills, ['Python', 'Django']);
  await respond(requests[1], item, true, 201);
  await respond(requests[2], [item]);
  get('search-input').value = 'Developer';
  for (const [action, method] of [['star', 'POST'], ['delete', 'DELETE']]) {
    const index = requests.length;
    clickAction(get, action);
    assert.equal(requests[index].options.method, method);
    assert.equal(requests[index].options.headers['X-CSRFToken'], 'test-token');
    await respond(requests[index], action === 'delete' ? null : item, true, action === 'delete' ? 204 : 200);
    assert.equal(requests[index + 1].url.searchParams.get('title'), 'Developer');
    await respond(requests[index + 1], []);
  }
});
