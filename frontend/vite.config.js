import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import fs from 'node:fs'
import path from 'node:path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
// #region agent log
const DEBUG_LOG = path.resolve(__dirname, '../debug-864821.log')
function scanMergeConflictMarkers(srcDir) {
  const found = []
  const walk = (d) => {
    if (!fs.existsSync(d)) return
    for (const ent of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, ent.name)
      if (ent.isDirectory()) {
        if (ent.name === 'node_modules') continue
        walk(p)
      } else if (/\.(vue|js|mjs|cjs|css|ts|tsx)$/.test(ent.name)) {
        const c = fs.readFileSync(p, 'utf8')
        if (c.includes('<<<<<<<')) {
          found.push(path.relative(path.join(__dirname, '..'), p).replace(/\\/g, '/'))
        }
      }
    }
  }
  walk(srcDir)
  return found
}
function debugMergeConflictScanPlugin() {
  return {
    name: 'debug-merge-conflict-scan',
    buildStart() {
      const conflicts = scanMergeConflictMarkers(path.join(__dirname, 'src'))
      const payload = {
        sessionId: '864821',
        timestamp: Date.now(),
        location: 'vite.config.js:debug-merge-conflict-scan',
        message: 'merge conflict marker scan',
        data: { conflictCount: conflicts.length, files: conflicts },
        hypothesisId: 'H1',
        runId: 'merge-scan',
      }
      try {
        fs.appendFileSync(DEBUG_LOG, `${JSON.stringify(payload)}\n`, 'utf8')
      } catch {
        /* ignore */
      }
      fetch('http://127.0.0.1:7813/ingest/3ff658d9-2454-4399-9401-162bba519fe7', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Debug-Session-Id': '864821',
        },
        body: JSON.stringify(payload),
      }).catch(() => {})
    },
  }
}
// #endregion

export default defineConfig({
  plugins: [debugMergeConflictScanPlugin(), vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
})
