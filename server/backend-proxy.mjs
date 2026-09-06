import http from 'node:http';
import https from 'node:https';

const hopHeaders = ['connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
  'te', 'trailer', 'transfer-encoding', 'upgrade'];

function endToEndHeaders(source) {
  const headers = { ...source };
  const connection = String(source.connection || '').split(',').map(s => s.trim().toLowerCase());
  for (const key of [...hopHeaders, ...connection]) delete headers[key];
  return headers;
}

export function createBackendProxy(backendUrl, { timeoutMs = 600_000 } = {}) {
  const backend = new URL(backendUrl);
  if (!['http:', 'https:'].includes(backend.protocol) || backend.username || backend.password ||
      backend.search || backend.hash || backend.pathname !== '/') {
    throw new Error('BACKEND_URL 必须是无凭据、无路径的 HTTP(S) 服务地址');
  }
  const transport = backend.protocol === 'https:' ? https : http;
  return (req, res) => {
    const headers = endToEndHeaders(req.headers);
    headers.host = backend.host;
    // Do not trust client-provided forwarding headers for auth rate limiting.
    delete headers.forwarded;
    headers['x-forwarded-for'] = req.socket.remoteAddress || '';
    headers['x-forwarded-host'] = req.headers.host || '';
    headers['x-forwarded-proto'] = req.socket.encrypted ? 'https' : 'http';
    const upstream = transport.request({
      protocol: backend.protocol, hostname: backend.hostname, port: backend.port,
      method: req.method, path: req.originalUrl || req.url, headers,
    }, response => {
      res.writeHead(response.statusCode || 502, endToEndHeaders(response.headers));
      res.flushHeaders();
      response.on('error', () => res.destroy());
      response.pipe(res);
    });
    upstream.setTimeout(timeoutMs, () => upstream.destroy(new Error('backend timeout')));
    upstream.on('error', () => {
      if (res.destroyed) return;
      if (res.headersSent) return res.destroy();
      res.writeHead(502, { 'content-type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ detail: '真实业务后端不可用，请检查 FastAPI 服务' }));
    });
    req.on('aborted', () => upstream.destroy());
    req.on('error', () => upstream.destroy());
    res.on('close', () => upstream.destroy());
    req.pipe(upstream);
  };
}
