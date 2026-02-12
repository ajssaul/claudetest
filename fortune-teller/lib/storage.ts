export interface UserSession {
  uuid: string
  birthYear: number
  birthMonth: number
  birthDay: number
  paid: boolean
  createdAt: string
}

const STORAGE_KEY = 'fortune_studio_session'

export function getSession(): UserSession | null {
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

export function createSession(year: number, month: number, day: number): UserSession {
  const session: UserSession = {
    uuid: crypto.randomUUID(),
    birthYear: year,
    birthMonth: month,
    birthDay: day,
    paid: false,
    createdAt: new Date().toISOString(),
  }

  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  }

  return session
}

export function updateSession(updates: Partial<UserSession>): UserSession | null {
  if (typeof window === 'undefined') return null

  const current = getSession()
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

export function isPaid(): boolean {
  return getSession()?.paid === true
}
