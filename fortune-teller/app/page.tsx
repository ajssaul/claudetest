'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowRight, Sparkles, Moon, Sun } from 'lucide-react'
import { getSession, createSession } from '@/lib/storage'

export default function HomePage() {
  const router = useRouter()
  const [year, setYear] = useState('')
  const [month, setMonth] = useState('')
  const [day, setDay] = useState('')
  const [isLoaded, setIsLoaded] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    const session = getSession()
    if (session?.paid) {
      router.push(`/results/${session.uuid}`)
      return
    }
    if (session) {
      setYear(String(session.birthYear))
      setMonth(String(session.birthMonth))
      setDay(String(session.birthDay))
    }
    setIsLoaded(true)
  }, [router])

  const isValidDate = () => {
    const y = parseInt(year)
    const m = parseInt(month)
    const d = parseInt(day)

    if (!y || !m || !d) return false
    if (y < 1920 || y > new Date().getFullYear()) return false
    if (m < 1 || m > 12) return false
    if (d < 1 || d > 31) return false

    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValidDate() || isSubmitting) return

    setIsSubmitting(true)
    createSession(parseInt(year), parseInt(month), parseInt(day))

    await new Promise(resolve => setTimeout(resolve, 300))
    router.push('/loading')
  }

  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="w-8 h-8 border border-black/20 rounded-full border-t-black animate-spin"
        />
      </div>
    )
  }

  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="py-8 px-8 md:px-16"
      >
        <div className="flex items-center justify-between">
          <h1 className="font-display text-lg md:text-xl tracking-widest uppercase">
            Fortune Studio
          </h1>
          <div className="flex items-center gap-2 text-muted">
            <Moon size={14} strokeWidth={1.25} />
            <Sun size={14} strokeWidth={1.25} />
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-8 md:px-16 pb-24">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2 }}
          className="text-center max-w-2xl mx-auto mb-16"
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="inline-flex items-center gap-2 px-4 py-2 border border-border rounded-full mb-12"
          >
            <Sparkles size={14} strokeWidth={1.25} />
            <span className="text-xs tracking-widest uppercase">Premium Fortune Reading</span>
          </motion.div>

          <h2 className="font-display text-4xl md:text-6xl lg:text-7xl leading-tight mb-8 tracking-tight">
            당신의 운명을
            <br />
            <span className="italic">발견하세요</span>
          </h2>

          <p className="font-body text-muted text-sm md:text-base leading-relaxed max-w-md mx-auto">
            생년월일에 담긴 우주의 메시지를 해독합니다.
            동양과 서양의 지혜가 만나 당신만의 운세를 전해드립니다.
          </p>
        </motion.div>

        {/* Birthdate Form */}
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="w-full max-w-lg"
        >
          <p className="text-center text-xs tracking-widest uppercase text-muted mb-8">
            생년월일을 입력하세요
          </p>

          <div className="flex gap-4 justify-center mb-12">
            {/* Year */}
            <div className="flex-1 max-w-[120px]">
              <input
                type="number"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                placeholder="1990"
                min="1920"
                max={new Date().getFullYear()}
                className="w-full bg-transparent border-b border-border py-4 text-center text-xl md:text-2xl font-display tracking-wide focus:border-black transition-colors"
              />
              <p className="text-center text-[10px] tracking-widest uppercase text-light mt-2">년</p>
            </div>

            {/* Month */}
            <div className="flex-1 max-w-[80px]">
              <input
                type="number"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
                placeholder="01"
                min="1"
                max="12"
                className="w-full bg-transparent border-b border-border py-4 text-center text-xl md:text-2xl font-display tracking-wide focus:border-black transition-colors"
              />
              <p className="text-center text-[10px] tracking-widest uppercase text-light mt-2">월</p>
            </div>

            {/* Day */}
            <div className="flex-1 max-w-[80px]">
              <input
                type="number"
                value={day}
                onChange={(e) => setDay(e.target.value)}
                placeholder="15"
                min="1"
                max="31"
                className="w-full bg-transparent border-b border-border py-4 text-center text-xl md:text-2xl font-display tracking-wide focus:border-black transition-colors"
              />
              <p className="text-center text-[10px] tracking-widest uppercase text-light mt-2">일</p>
            </div>
          </div>

          <motion.button
            type="submit"
            disabled={!isValidDate() || isSubmitting}
            whileHover={{ scale: isValidDate() ? 1.02 : 1 }}
            whileTap={{ scale: isValidDate() ? 0.98 : 1 }}
            className={`
              w-full py-5 px-8
              flex items-center justify-center gap-3
              text-sm tracking-widest uppercase
              transition-all duration-500 btn-luxury
              ${isValidDate()
                ? 'bg-black text-white cursor-pointer'
                : 'bg-border text-muted cursor-not-allowed'
              }
            `}
          >
            {isSubmitting ? (
              <span className="flex items-center gap-3">
                <motion.span
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-4 h-4 border border-white/30 border-t-white rounded-full"
                />
                분석 중...
              </span>
            ) : (
              <>
                나의 운세 확인하기
                <ArrowRight size={16} strokeWidth={1.25} />
              </>
            )}
          </motion.button>
        </motion.form>

        {/* Preview Icons */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1 }}
          className="mt-20 flex items-center justify-center gap-8 text-4xl"
        >
          <motion.span animate={{ y: [0, -5, 0] }} transition={{ duration: 2, repeat: Infinity, delay: 0 }}>
            ♈
          </motion.span>
          <motion.span animate={{ y: [0, -5, 0] }} transition={{ duration: 2, repeat: Infinity, delay: 0.3 }}>
            🐉
          </motion.span>
          <motion.span animate={{ y: [0, -5, 0] }} transition={{ duration: 2, repeat: Infinity, delay: 0.6 }}>
            ☯
          </motion.span>
          <motion.span animate={{ y: [0, -5, 0] }} transition={{ duration: 2, repeat: Infinity, delay: 0.9 }}>
            🌙
          </motion.span>
        </motion.div>
      </div>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.8 }}
        className="py-8 px-8 md:px-16 border-t border-border"
      >
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-xs tracking-widest uppercase text-muted">
          <span>동양 & 서양 운세 통합</span>
          <span>띠 · 별자리 · 수비학</span>
        </div>
      </motion.footer>
    </main>
  )
}
