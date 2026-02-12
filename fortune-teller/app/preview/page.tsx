'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Lock, CreditCard, Shield, ArrowLeft, Check, Star } from 'lucide-react'
import { getSession, markAsPaid } from '@/lib/storage'
import { getChineseZodiac, getWesternZodiac, getLifePathNumber, LIFE_PATH_MEANINGS, getCompatibilityScore } from '@/lib/fortune'

export default function PreviewPage() {
  const router = useRouter()
  const [session, setSession] = useState<ReturnType<typeof getSession>>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    const s = getSession()
    if (!s) {
      router.push('/')
      return
    }
    if (s.paid) {
      router.push(`/results/${s.uuid}`)
      return
    }
    setSession(s)
    setIsLoaded(true)
  }, [router])

  const handlePayment = async () => {
    setIsProcessing(true)
    await new Promise(resolve => setTimeout(resolve, 1500))
    const updated = markAsPaid()
    if (updated) {
      router.push(`/results/${updated.uuid}`)
    }
  }

  if (!isLoaded || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div className="w-8 h-8 border border-black/20 rounded-full border-t-black animate-spin" />
      </div>
    )
  }

  const chineseZodiac = getChineseZodiac(session.birthYear)
  const westernZodiac = getWesternZodiac(session.birthMonth, session.birthDay)
  const lifePath = getLifePathNumber(session.birthYear, session.birthMonth, session.birthDay)
  const lifePathMeaning = LIFE_PATH_MEANINGS[lifePath] || LIFE_PATH_MEANINGS[1]
  const scores = getCompatibilityScore(lifePath)

  return (
    <main className="min-h-screen flex flex-col bg-white">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="py-8 px-8 md:px-16 border-b border-border"
      >
        <div className="flex items-center justify-between">
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-muted hover:text-primary transition-colors"
          >
            <ArrowLeft size={16} strokeWidth={1.25} />
            <span className="text-xs tracking-widest uppercase">Back</span>
          </button>
          <h1 className="font-display text-lg tracking-widest uppercase">Fortune Studio</h1>
          <div className="w-16" />
        </div>
      </motion.header>

      <div className="flex-1 px-8 md:px-16 py-12 md:py-16">
        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h2 className="font-display text-3xl md:text-4xl mb-4">
            당신의 운세가 준비되었습니다
          </h2>
          <p className="text-sm text-muted">
            {session.birthYear}년 {session.birthMonth}월 {session.birthDay}일생
          </p>
        </motion.div>

        {/* Preview Cards - Blurred */}
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {/* Chinese Zodiac Card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="border border-border p-8 relative overflow-hidden"
          >
            <div className="blur-preview">
              <p className="text-6xl mb-4">{chineseZodiac.emoji}</p>
              <h3 className="font-display text-2xl mb-2">{chineseZodiac.animal}띠</h3>
              <p className="text-sm text-muted">{chineseZodiac.trait}</p>
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-white via-white/50 to-transparent" />
            <div className="absolute bottom-4 left-0 right-0 text-center">
              <Lock size={16} className="inline-block text-muted" />
            </div>
          </motion.div>

          {/* Western Zodiac Card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="border border-border p-8 relative overflow-hidden"
          >
            <div className="blur-preview">
              <p className="text-6xl mb-4">{westernZodiac.emoji}</p>
              <h3 className="font-display text-2xl mb-2">{westernZodiac.sign}</h3>
              <p className="text-sm text-muted">{westernZodiac.trait}</p>
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-white via-white/50 to-transparent" />
            <div className="absolute bottom-4 left-0 right-0 text-center">
              <Lock size={16} className="inline-block text-muted" />
            </div>
          </motion.div>

          {/* Life Path Card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="border border-border p-8 relative overflow-hidden"
          >
            <div className="blur-preview">
              <p className="text-6xl font-display mb-4">{lifePath}</p>
              <h3 className="font-display text-2xl mb-2">생명수 - {lifePathMeaning.title}</h3>
              <p className="text-sm text-muted line-clamp-2">{lifePathMeaning.description}</p>
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-white via-white/50 to-transparent" />
            <div className="absolute bottom-4 left-0 right-0 text-center">
              <Lock size={16} className="inline-block text-muted" />
            </div>
          </motion.div>

          {/* Compatibility Score Card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="border border-border p-8 relative overflow-hidden"
          >
            <div className="blur-preview">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-3xl font-display">{scores.love}%</p>
                  <p className="text-xs text-muted">연애운</p>
                </div>
                <div>
                  <p className="text-3xl font-display">{scores.career}%</p>
                  <p className="text-xs text-muted">직장운</p>
                </div>
                <div>
                  <p className="text-3xl font-display">{scores.health}%</p>
                  <p className="text-xs text-muted">건강운</p>
                </div>
                <div>
                  <p className="text-3xl font-display">{scores.wealth}%</p>
                  <p className="text-xs text-muted">재물운</p>
                </div>
              </div>
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-white via-white/50 to-transparent" />
            <div className="absolute bottom-4 left-0 right-0 text-center">
              <Lock size={16} className="inline-block text-muted" />
            </div>
          </motion.div>
        </div>

        {/* Payment Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="max-w-md mx-auto"
        >
          <div className="bg-white border border-border p-8 md:p-12 text-center">
            <p className="text-xs tracking-widest uppercase text-muted mb-4">Premium Fortune Reading</p>
            <div className="flex items-baseline justify-center gap-1 mb-2">
              <span className="font-display text-5xl">₩9,900</span>
            </div>
            <p className="text-xs text-muted mb-8">1회 결제</p>

            <div className="space-y-3 text-left mb-8">
              {[
                '띠 & 별자리 상세 분석',
                '생명수(수비학) 해석',
                '오늘의 운세 3가지',
                '운세 점수 (연애/직장/건강/재물)',
                '행운의 색상/숫자/방향',
                '영구 저장 & 무제한 열람'
              ].map((feature, i) => (
                <div key={i} className="flex items-center gap-3">
                  <Check size={14} strokeWidth={1.5} className="text-primary flex-shrink-0" />
                  <span className="text-sm text-muted">{feature}</span>
                </div>
              ))}
            </div>

            <motion.button
              onClick={handlePayment}
              disabled={isProcessing}
              whileHover={{ scale: !isProcessing ? 1.02 : 1 }}
              whileTap={{ scale: !isProcessing ? 0.98 : 1 }}
              className="w-full py-5 bg-black text-white flex items-center justify-center gap-3 text-sm tracking-widest uppercase btn-luxury"
            >
              <AnimatePresence mode="wait">
                {isProcessing ? (
                  <motion.span
                    key="processing"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-3"
                  >
                    <Lock size={14} strokeWidth={1.25} className="animate-pulse" />
                    보안 결제 처리 중...
                  </motion.span>
                ) : (
                  <motion.span
                    key="pay"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-3"
                  >
                    <CreditCard size={14} strokeWidth={1.25} />
                    운세 잠금 해제하기
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>
          </div>

          <div className="flex items-center justify-center gap-8 mt-6 text-muted">
            <div className="flex items-center gap-2">
              <Shield size={14} strokeWidth={1.25} />
              <span className="text-[10px] tracking-widest uppercase">안전 결제</span>
            </div>
            <div className="flex items-center gap-2">
              <Star size={14} strokeWidth={1.25} />
              <span className="text-[10px] tracking-widest uppercase">즉시 열람</span>
            </div>
          </div>
        </motion.div>
      </div>

      <footer className="py-6 px-8 border-t border-border">
        <p className="text-center text-[10px] tracking-widest uppercase text-light">
          Demo Mode — 실제 결제 없이 진행됩니다
        </p>
      </footer>
    </main>
  )
}
