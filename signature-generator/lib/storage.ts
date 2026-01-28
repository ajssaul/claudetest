export interface UserSession {
  uuid: string
  name: string
  paid: boolean
  selectedStyle: number
  createdAt: string
}

const STORAGE_KEY = 'signature_studio_session'

export function getOrCreateSession(): UserSession | null {
  if (typeof window === 'undefined') return null

  const stored = localStorage.getItem(STORAGE_KEY)

  if (stored) {
    try {
      return JSON.parse(stored) as UserSession
    } catch {
      return null
    }
  }

  return null
}

export function createNewSession(name: string): UserSession {
  const session: UserSession = {
    uuid: crypto.randomUUID(),
    name,
    paid: false,
    selectedStyle: 0,
    createdAt: new Date().toISOString(),
  }

  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  }

  return session
}

export function updateSession(updates: Partial<UserSession>): UserSession | null {
  if (typeof window === 'undefined') return null

  const current = getOrCreateSession()
  if (!current) return null

  const updated = { ...current, ...updates }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))

  return updated
}

export function markAsPaid(): UserSession | null {
  return updateSession({ paid: true })
}

export function clearSession(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(STORAGE_KEY)
  }
}

export function hasValidSession(): boolean {
  const session = getOrCreateSession()
  return session !== null && session.name.length > 0
}

export function isPaid(): boolean {
  const session = getOrCreateSession()
  return session?.paid === true
}
