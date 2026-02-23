/**
 * papadam crdt — y-websocket sync server
 *
 * Responsibilities:
 *  1. Authenticate connecting clients (JWT → Django API)
 *  2. Check group membership before allowing doc access
 *  3. Load Y.js binary state from Django on first doc access
 *  4. Persist Y.js binary state + normalized records to Django on update
 *  5. Fan-out awareness (presence) via Redis pub/sub for multi-instance support
 */

import { WebSocketServer } from 'ws'
import * as Y from 'yjs'
import axios from 'axios'
import { Redis } from 'ioredis'

const PORT = parseInt(process.env.PORT ?? '1234')
const API_URL = process.env.API_URL ?? 'http://api:8000'
const REDIS_URL = process.env.REDIS_URL ?? 'redis://redis:6379'

const redis = new Redis(REDIS_URL)
const wss = new WebSocketServer({ port: PORT })

// TODO Phase 2: implement full y-websocket server with:
//   - JWT validation on upgrade (ws.on('headers'))
//   - group membership check via GET /api/v1/group/{groupId}/
//   - persistence adapter: GET/PUT /api/v1/crdt/media/{uuid}/
//   - Redis pub/sub for multi-instance awareness fan-out
//   - structured logging (JSON to stdout)

wss.on('listening', () => {
  console.log(JSON.stringify({ level: 'info', msg: 'crdt server listening', port: PORT }))
})

wss.on('error', (err) => {
  console.error(JSON.stringify({ level: 'error', msg: 'crdt server error', error: err.message }))
})

export {}
