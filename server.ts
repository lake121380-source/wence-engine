import express from 'express';
import path from 'node:path';
import fs from 'node:fs';
import { createServer as createViteServer } from 'vite';
import { createBackendProxy } from './server/backend-proxy.mjs';

// FastAPI owns every API, identity and stored record. Node only serves the UI.
const app = express();
const port = Number(process.env.PORT || 3002);
const host = process.env.HOST || '127.0.0.1';
const backendUrl = process.env.BACKEND_URL || process.env.LEGACY_BACKEND_URL || 'http://127.0.0.1:8000';
const proxy = createBackendProxy(backendUrl);
// Before any body parser: preserve multipart boundaries and stream SSE directly.
app.use('/api', proxy);
app.use('/health', proxy);

async function start() {
  if (process.env.NODE_ENV !== 'production') {
    const admin = await createViteServer({
      root: path.resolve('content-studio/admin'), base: '/admin/',
      server: { middlewareMode: true, hmr: false }, appType: 'spa',
    });
    app.use('/admin', admin.middlewares);
    const frontend = await createViteServer({
      root: path.resolve('content-studio/frontend'),
      server: { middlewareMode: true, hmr: false }, appType: 'spa',
    });
    app.use(frontend.middlewares);
  } else {
    const client = path.resolve('dist/client');
    const admin = path.join(client, 'admin');
    for (const dir of [client, admin]) {
      if (!fs.existsSync(path.join(dir, 'index.html'))) throw new Error('请先执行 npm run build');
    }
    // Express treats `/admin` and `/admin/` as the same route by default.
    // Guard the redirect so `/admin/` can fall through to the static index
    // instead of redirecting to itself forever.
    app.get('/admin', (req, res, next) => {
      if (req.path === '/admin') return res.redirect('/admin/');
      next();
    });
    app.use('/admin', express.static(admin));
    app.get('/admin/*', (_req, res) => res.sendFile(path.join(admin, 'index.html')));
    app.use(express.static(client));
    app.get('*', (_req, res) => res.sendFile(path.join(client, 'index.html')));
  }
  app.listen(port, host, () => console.log(`文策引擎 http://${host}:${port} → FastAPI ${backendUrl}`));
}

start().catch(error => { console.error(error); process.exitCode = 1; });
