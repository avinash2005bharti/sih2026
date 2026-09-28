/**
 * Centralized Valkey Cache Service for Sovereign AI Workbench (Node.js Backend)
 * SIH 26117
 *
 * Uses ioredis (already installed in package.json) to connect to Valkey.
 * Valkey is Redis-protocol compatible so ioredis works natively.
 *
 * Operates in graceful degraded mode if Valkey is unavailable.
 */

const Redis = require("ioredis");
const crypto = require("crypto");

const VALKEY_URL = process.env.VALKEY_URL || "redis://localhost:6379";
const PROJECT_PREFIX = "sih26117:v1";

// TTL constants (seconds)
const TTL = {
  ROUTE: 300,       // 5 min
  RAG: 600,         // 10 min
  SESSION: 3600,    // 1 hour
  RATE_LIMIT: 60,   // 1 min
  SHORT: 60,        // 1 min
};

/**
 * Build a namespaced cache key.
 * @param {...string} parts
 * @returns {string}
 */
function makeKey(...parts) {
  return [PROJECT_PREFIX, ...parts].join(":");
}

/**
 * SHA-256 hash of text, truncated to 16 hex chars.
 * @param {string} text
 * @returns {string}
 */
function hashText(text) {
  return crypto.createHash("sha256").update(text, "utf8").digest("hex").slice(0, 16);
}

class CacheService {
  constructor() {
    this._client = null;
    this._connected = false;
    this._enabled = false;

    // Stats
    this._hits = 0;
    this._misses = 0;
    this._sets = 0;
    this._errors = 0;

    this._connect();
  }

  _connect() {
    try {
      this._client = new Redis(VALKEY_URL, {
        lazyConnect: false,
        connectTimeout: 3000,
        commandTimeout: 3000,
        maxRetriesPerRequest: 1,
        retryStrategy: (times) => {
          if (times > 3) return null; // Stop retrying after 3 attempts
          return Math.min(times * 200, 1000);
        },
        enableReadyCheck: true,
      });

      this._client.on("connect", () => {
        this._connected = true;
        this._enabled = true;
        console.log(`[CACHE] ✅ Valkey connected at ${VALKEY_URL}`);
      });

      this._client.on("error", (err) => {
        if (this._connected) {
          console.warn(`[CACHE] Valkey error: ${err.message} — degraded mode`);
        }
        this._connected = false;
        this._enabled = false;
        this._errors++;
      });

      this._client.on("close", () => {
        this._connected = false;
        this._enabled = false;
      });

      this._client.on("reconnecting", () => {
        console.log("[CACHE] Valkey reconnecting...");
      });
    } catch (err) {
      console.warn(`[CACHE] Valkey init failed: ${err.message} — degraded mode`);
      this._enabled = false;
      this._connected = false;
    }
  }

  get isAvailable() {
    return this._enabled && this._connected && this._client !== null;
  }

  /**
   * Get a cached value by key. Returns null on miss or error.
   * @param {string} key
   * @returns {Promise<any|null>}
   */
  async get(key) {
    if (!this.isAvailable) return null;
    try {
      const raw = await this._client.get(key);
      if (raw === null) {
        this._misses++;
        return null;
      }
      this._hits++;
      return JSON.parse(raw);
    } catch (err) {
      this._errors++;
      return null;
    }
  }

  /**
   * Set a cache value with TTL in seconds.
   * @param {string} key
   * @param {any} value
   * @param {number} ttl
   * @returns {Promise<boolean>}
   */
  async set(key, value, ttl = TTL.ROUTE) {
    if (!this.isAvailable) return false;
    try {
      await this._client.setex(key, ttl, JSON.stringify(value));
      this._sets++;
      return true;
    } catch (err) {
      this._errors++;
      return false;
    }
  }

  /**
   * Delete a key.
   * @param {string} key
   * @returns {Promise<boolean>}
   */
  async delete(key) {
    if (!this.isAvailable) return false;
    try {
      await this._client.del(key);
      return true;
    } catch (err) {
      return false;
    }
  }

  /**
   * Check if a key exists.
   * @param {string} key
   * @returns {Promise<boolean>}
   */
  async exists(key) {
    if (!this.isAvailable) return false;
    try {
      return (await this._client.exists(key)) === 1;
    } catch (err) {
      return false;
    }
  }

  /**
   * Get or set a cached value using a factory function.
   * @param {string} key
   * @param {Function} factory - async function that returns the value
   * @param {number} ttl
   * @returns {Promise<{value: any, cacheHit: boolean}>}
   */
  async getOrSet(key, factory, ttl = TTL.ROUTE) {
    const cached = await this.get(key);
    if (cached !== null) {
      return { value: cached, cacheHit: true };
    }
    const value = await factory();
    if (value !== null && value !== undefined) {
      await this.set(key, value, ttl);
    }
    return { value, cacheHit: false };
  }

  /**
   * Ping Valkey and return round-trip latency in ms. Returns -1 if unavailable.
   * @returns {Promise<number>}
   */
  async ping() {
    if (!this.isAvailable) return -1;
    try {
      const start = Date.now();
      await this._client.ping();
      return Date.now() - start;
    } catch (err) {
      return -1;
    }
  }

  /**
   * Return cache statistics.
   * @returns {Object}
   */
  getStats() {
    const total = this._hits + this._misses;
    return {
      connected: this._connected,
      enabled: this._enabled,
      hits: this._hits,
      misses: this._misses,
      sets: this._sets,
      errors: this._errors,
      hit_rate_pct: total > 0 ? Math.round((this._hits / total) * 1000) / 10 : 0,
      total_requests: total,
      url: VALKEY_URL,
    };
  }

  /**
   * Close the connection gracefully.
   */
  async close() {
    if (this._client) {
      await this._client.quit().catch(() => this._client.disconnect());
      this._client = null;
      this._connected = false;
    }
  }
}

// Key helpers for Node backend
function sessionKey(sessionId) {
  return makeKey("session", sessionId);
}
function rateKey(userId) {
  return makeKey("rate", userId);
}
function userKey(userId, scope) {
  return makeKey("user", userId, scope);
}

// Global singleton
const cacheService = new CacheService();

module.exports = {
  cacheService,
  makeKey,
  hashText,
  sessionKey,
  rateKey,
  userKey,
  TTL,
};
