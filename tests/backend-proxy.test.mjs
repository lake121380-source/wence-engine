import { test } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { once } from 'node:events';
import { createBackendProxy } from '../server/backend-proxy.mjs';

async function listen(t, handler) {
  const server = http.createServer(handler).listen(0, '127.0.0.1');
  await once(server, 'listening');
  t.after(() => { server.closeAllConnections(); server.close(); });
  return `http://127.0.0.1:${server.address().port}`;
}

test('auth failures, tokens, cookies and redirects pass through without fallback', async t => {
  const backend = await listen(t, (req, res) => {
    assert.notEqual(req.headers['x-forwarded-for'], 'attacker');
    if (req.url === '/api/auth/login') {
      res.writeHead(401, { 'content-type': 'application/json', 'set-cookie': ['a=1', 'b=2'] });
      return res.end('{"detail":"bad password"}');
    }
    if (req.url === '/api/auth/callback') {
      res.writeHead(302, { location: '/login?code=test' }); return res.end();
    }
    res.writeHead(req.headers.authorization === 'Bearer actual-user-token' ? 200 : 401);
    res.end(req.headers.authorization || 'anonymous');
  });
  const gateway = await listen(t, createBackendProxy(backend));
  assert.equal((await fetch(gateway + '/api/creators')).status, 401);
  assert.equal((await fetch(gateway + '/api/creators', { headers: { authorization: 'Bearer forged-email-claim' } })).status, 401);
  assert.equal(await (await fetch(gateway + '/api/creators', { headers: { authorization: 'Bearer actual-user-token' } })).text(), 'Bearer actual-user-token');
  const login = await fetch(gateway + '/api/auth/login', { method: 'POST', headers: { 'x-forwarded-for': 'attacker' } });
  assert.equal(login.status, 401);
  assert.deepEqual(login.headers.getSetCookie(), ['a=1', 'b=2']);
  assert.equal((await login.json()).detail, 'bad password');
  const redirect = await fetch(gateway + '/api/auth/callback', { redirect: 'manual' });
  assert.equal(redirect.status, 302);
  assert.equal(redirect.headers.get('location'), '/login?code=test');
});

test('multipart bytes, query strings, binary responses and empty 204 remain intact', async t => {
  const payload = Buffer.from('--boundary\r\nContent-Disposition: form-data; name="file"; filename="test.pdf"\r\n\r\n%PDF-1.7\u0000\u00ff\r\n--boundary--\r\n');
  const backend = await listen(t, async (req, res) => {
    if (req.method === 'DELETE') { res.writeHead(204); return res.end(); }
    assert.equal(req.url, '/api/documents/upload?folder=%E4%BA%A7%E5%93%81');
    assert.equal(req.headers['content-type'], 'multipart/form-data; boundary=boundary');
    const chunks = []; for await (const chunk of req) chunks.push(chunk);
    assert.deepEqual(Buffer.concat(chunks), payload);
    res.writeHead(200, { 'content-type': 'application/octet-stream', 'content-length': payload.length });
    res.end(payload);
  });
  const gateway = await listen(t, createBackendProxy(backend));
  const response = await fetch(gateway + '/api/documents/upload?folder=%E4%BA%A7%E5%93%81', { method: 'POST', headers: { 'content-type': 'multipart/form-data; boundary=boundary' }, body: payload });
  assert.deepEqual(Buffer.from(await response.arrayBuffer()), payload);
  assert.equal((await fetch(gateway + '/api/documents/1', { method: 'DELETE' })).status, 204);
});

test('SSE first event reaches client before backend completes; disconnect cancels upstream', { timeout: 5000 }, async t => {
  let finish;
  let closed;
  const disconnected = new Promise(resolve => { closed = resolve; });
  const backend = await listen(t, (_req, res) => {
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    res.write('event: delta\ndata: "第一段"\n\n');
    finish = () => res.end('event: done\ndata: {}\n\n');
    res.on('close', () => closed());
  });
  const gateway = await listen(t, createBackendProxy(backend));
  const response = await fetch(gateway + '/api/generate/stream', { method: 'POST' });
  const reader = response.body.getReader();
  const first = await reader.read();
  assert.match(new TextDecoder().decode(first.value), /第一段/);
  assert.equal(first.done, false);
  finish();
  const second = await reader.read();
  assert.match(new TextDecoder().decode(second.value), /event: done/);
  await reader.cancel();
  await disconnected;
  const aborted = await fetch(gateway + '/api/generate/stream', { method: 'POST' });
  const abortReader = aborted.body.getReader();
  await abortReader.read();
  const upstreamClosed = new Promise(resolve => { closed = resolve; });
  await abortReader.cancel();
  await upstreamClosed;
});

test('unavailable backend returns 502, never demonstration data', async t => {
  const temporary = http.createServer().listen(0, '127.0.0.1');
  await once(temporary, 'listening');
  const port = temporary.address().port;
  await new Promise(resolve => temporary.close(resolve));
  const gateway = await listen(t, createBackendProxy(`http://127.0.0.1:${port}`));
  const response = await fetch(gateway + '/api/creators');
  assert.equal(response.status, 502);
  assert.match((await response.json()).detail, /真实业务后端不可用/);
});
