export interface UserSession {
  uuid: string
  birthYear: number
  birthMonth: number
  birthDay: number
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
    createdAt: new Date().toISOString(),
  }

  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  }

  return session
}

export function clearSession(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(STORAGE_KEY)
  }
}
