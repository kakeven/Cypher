import { Capacitor } from '@capacitor/core'
import { SecureStorage } from '@aparajita/capacitor-secure-storage'

let database

async function databaseSecret() {
  let secret = await SecureStorage.getItem('cypher.database.secret')
  if (secret) return secret
  secret = `${crypto.randomUUID()}${crypto.randomUUID()}`
  await SecureStorage.setItem('cypher.database.secret', secret)
  return secret
}

export async function initializeMobileDatabase() {
  if (!Capacitor.isNativePlatform()) return null
  if (database) return database

  const { CapacitorSQLite, SQLiteConnection } = await import('@capacitor-community/sqlite')
  const connection = new SQLiteConnection(CapacitorSQLite)
  const secret = await databaseSecret()
  const stored = await connection.isSecretStored()
  if (!stored.result) await connection.setEncryptionSecret(secret)
  database = await connection.createConnection('cypher', true, 'secret', 1, false)
  await database.open()
  await database.execute(`
    CREATE TABLE IF NOT EXISTS response_cache (
      key TEXT PRIMARY KEY NOT NULL,
      body TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
  `)
  await database.execute(`
    CREATE TABLE IF NOT EXISTS app_state (
      id INTEGER PRIMARY KEY CHECK (id = 1),
      body TEXT NOT NULL
    );
  `)
  return database
}

export async function cacheResponse(key, body) {
  const db = await initializeMobileDatabase()
  if (!db) return
  await db.run(
    'INSERT OR REPLACE INTO response_cache (key, body, updated_at) VALUES (?, ?, ?)',
    [key, JSON.stringify(body), new Date().toISOString()],
  )
}

export async function readCachedResponse(key) {
  const db = await initializeMobileDatabase()
  if (!db) return undefined
  const result = await db.query('SELECT body FROM response_cache WHERE key = ?', [key])
  return result.values?.[0] ? JSON.parse(result.values[0].body) : undefined
}

const storageKey = 'cypher.mobile.local-state'

export async function readLocalState() {
  const fallback = localStorage.getItem(storageKey)
  if (!Capacitor.isNativePlatform()) return fallback ? JSON.parse(fallback) : null
  const db = await initializeMobileDatabase()
  const result = await db.query('SELECT body FROM app_state WHERE id = 1')
  return result.values?.[0] ? JSON.parse(result.values[0].body) : null
}

export async function writeLocalState(state) {
  if (!Capacitor.isNativePlatform()) {
    localStorage.setItem(storageKey, JSON.stringify(state))
    return
  }
  const db = await initializeMobileDatabase()
  await db.run('INSERT OR REPLACE INTO app_state (id, body) VALUES (1, ?)', [JSON.stringify(state)])
}
