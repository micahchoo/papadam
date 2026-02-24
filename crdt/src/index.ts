/**
 * papadam crdt — y-websocket sync server
 *
 * Responsibilities:
 *  1. Authenticate connecting clients — JWT verified via Django /auth/users/me/
 *  2. Check group membership before allowing doc access
 *  3. Load Y.js binary state from Django on first doc access
 *  4. Persist Y.js binary state to Django on update (debounced, 2 s)
 *  5. Redis connection kept for future multi-instance awareness fan-out
 *
 * URL format: ws://host/<mediaUuid>?token=<jwt>&groupId=<groupId>
 */

import { createServer } from 'node:http'
import { createRequire } from 'node:module'
import type { IncomingMessage, ServerResponse } from 'node:http'
import { WebSocketServer } from 'ws'
import type { WebSocket } from 'ws'
import * as Y from 'yjs'
import axios from 'axios'
import { Redis } from 'ioredis'

// ── Config ────────────────────────────────────────────────────────────────────

const PORT = parseInt(process.env['PORT'] ?? '1234', 10)
const API_URL = (process.env['CRDT_API_URL'] ?? 'http://api:8000').replace(/\/$/, '')
const REDIS_URL = process.env['REDIS_URL'] ?? 'redis://redis:6379'
// Service-account token used for server→Django persistence calls (required for state persist)
const SERVER_TOKEN = process.env['CRDT_SERVER_TOKEN'] ?? ''
// Debounce window for persistence writes (ms)
const PERSIST_DEBOUNCE_MS = 2000

// ── Logging ───────────────────────────────────────────────────────────────────

function log(
  level: 'info' | 'warn' | 'error',
  msg: string,
  extra?: Record<string, unknown>,
): void {
  process.stdout.write(
    JSON.stringify({ ts: new Date().toISOString(), level, msg, ...extra }) + '\n',
  )
}

// ── y-websocket server utilities (CJS module) ─────────────────────────────────

const _require = createRequire(import.meta.url)
const {
  setupWSConnection,
  setPersistence,
} = _require('y-websocket/bin/utils') as {
  setupWSConnection(
    conn: WebSocket,
    req: IncomingMessage,
    opts?: { docName?: string; gc?: boolean },
  ): void
  setPersistence(opts: {
    bindState(docName: string, ydoc: Y.Doc): Promise<void>
    writeState(docName: string, ydoc: Y.Doc): Promise<void>
    provider: null
  }): void
}

// ── Redis ─────────────────────────────────────────────────────────────────────

const redis = new Redis(REDIS_URL, { lazyConnect: true })
redis.on('error', (err: Error) => log('error', 'redis error', { error: err.message }))
void redis.connect().catch(() => log('warn', 'redis unavailable — multi-instance awareness disabled'))

// ── Django API helpers ────────────────────────────────────────────────────────

interface DjangoUser {
  id: number
  username: string
}

async function verifyToken(token: string): Promise<{ id: string; username: string } | null> {
  try {
    const { data } = await axios.get<DjangoUser>(`${API_URL}/auth/users/me/`, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 5000,
    })
    return { id: String(data.id), username: data.username }
  } catch {
    return null
  }
}

async function checkGroupMembership(token: string, groupId: string): Promise<boolean> {
  try {
    await axios.get(`${API_URL}/api/v1/group/${groupId}/`, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 5000,
    })
    return true
  } catch {
    return false
  }
}

// ── Persistence adapter ───────────────────────────────────────────────────────

const persistTimers = new Map<string, ReturnType<typeof setTimeout>>()

setPersistence({
  async bindState(docName: string, ydoc: Y.Doc): Promise<void> {
    if (!SERVER_TOKEN) return
    const uuid = docName.split(':')[1]
    if (!uuid) return
    try {
      const { data } = await axios.get<ArrayBuffer>(
        `${API_URL}/api/v1/crdt/media/${uuid}/`,
        {
          headers: { Authorization: `Bearer ${SERVER_TOKEN}` },
          responseType: 'arraybuffer',
          timeout: 10_000,
        },
      )
      if (data.byteLength > 0) {
        Y.applyUpdate(ydoc, new Uint8Array(data))
        log('info', 'doc state loaded', { docName, bytes: data.byteLength })
      }
    } catch {
      // New doc — no prior state; that is expected
    }
  },

  async writeState(docName: string, ydoc: Y.Doc): Promise<void> {
    if (!SERVER_TOKEN) return
    const uuid = docName.split(':')[1]
    if (!uuid) return

    // Debounce: cancel any pending write for this doc
    const existing = persistTimers.get(docName)
    if (existing) clearTimeout(existing)

    await new Promise<void>((resolve) => {
      persistTimers.set(
        docName,
        setTimeout(async () => {
          persistTimers.delete(docName)
          const update = Y.encodeStateAsUpdate(ydoc)
          try {
            await axios.put(`${API_URL}/api/v1/crdt/media/${uuid}/`, update, {
              headers: {
                Authorization: `Bearer ${SERVER_TOKEN}`,
                'Content-Type': 'application/octet-stream',
              },
              timeout: 10_000,
            })
            log('info', 'doc state persisted', { docName, bytes: update.byteLength })
          } catch (err: unknown) {
            log('error', 'persist failed', {
              docName,
              error: err instanceof Error ? err.message : String(err),
            })
          }
          resolve()
        }, PERSIST_DEBOUNCE_MS),
      )
    })
  },

  provider: null,
})

// ── Request parsing ───────────────────────────────────────────────────────────

interface UpgradeParams {
  token: string
  mediaUuid: string
  groupId: string
}

function parseUpgradeRequest(req: IncomingMessage): UpgradeParams | null {
  const url = new URL(req.url ?? '/', `http://${req.headers['host'] ?? 'localhost'}`)
  const token = url.searchParams.get('token') ?? ''
  const groupId = url.searchParams.get('groupId') ?? ''
  // Path: /<mediaUuid>
  const mediaUuid = url.pathname.replace(/^\//, '')
  if (!token || !groupId || !mediaUuid) return null
  return { token, mediaUuid, groupId }
}

// ── Augmented IncomingMessage ─────────────────────────────────────────────────

interface AuthedRequest extends IncomingMessage {
  parsedMediaUuid: string
  parsedUserId: string
  parsedUsername: string
}

// ── WebSocket server ──────────────────────────────────────────────────────────

const wss = new WebSocketServer({ noServer: true })

wss.on('connection', (ws: WebSocket, req: IncomingMessage) => {
  const { parsedMediaUuid, parsedUserId, parsedUsername } = req as AuthedRequest
  const docName = `media:${parsedMediaUuid}`

  log('info', 'client connected', {
    mediaUuid: parsedMediaUuid,
    userId: parsedUserId,
    username: parsedUsername,
  })

  setupWSConnection(ws, req, { docName, gc: true })

  ws.on('close', () => {
    log('info', 'client disconnected', {
      mediaUuid: parsedMediaUuid,
      userId: parsedUserId,
    })
  })
})

// ── HTTP server (handles WS upgrade with auth) ────────────────────────────────

const httpServer = createServer((req: IncomingMessage, res: ServerResponse) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end('{"status":"ok"}\n')
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' })
    res.end('not found\n')
  }
})

httpServer.on('upgrade', (req: IncomingMessage, socket, head) => {
  const params = parseUpgradeRequest(req)
  if (!params) {
    socket.write('HTTP/1.1 400 Bad Request\r\n\r\n')
    socket.destroy()
    return
  }

  // Auth is async — handle in a void IIFE
  void (async () => {
    const user = await verifyToken(params.token)
    if (!user) {
      socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n')
      socket.destroy()
      return
    }

    const allowed = await checkGroupMembership(params.token, params.groupId)
    if (!allowed) {
      socket.write('HTTP/1.1 403 Forbidden\r\n\r\n')
      socket.destroy()
      return
    }

    // Attach user info for the 'connection' handler
    ;(req as AuthedRequest).parsedMediaUuid = params.mediaUuid
    ;(req as AuthedRequest).parsedUserId = user.id
    ;(req as AuthedRequest).parsedUsername = user.username

    wss.handleUpgrade(req, socket, head, (ws) => {
      wss.emit('connection', ws, req)
    })
  })()
})

httpServer.listen(PORT, () => {
  log('info', 'crdt server listening', { port: PORT })
})

httpServer.on('error', (err: Error) => {
  log('error', 'http server error', { error: err.message })
  process.exit(1)
})
