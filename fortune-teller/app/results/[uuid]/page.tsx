'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { RefreshCw, Home, Sparkles, Heart, Briefcase, Activity, Coins } from 'lucide-react'
import { getSession, clearSession } from '@/lib/storage'
import {
  getChineseZodiac,
  getWesternZodiac,
  getLifePathNumber,
  LIFE_PATH_MEANINGS,
  getCompatibilityScore,
  generateDailyFortune,
  getLuckyInfo
} from '@/lib/fortune'

export default function ResultsPage() {
  const router = useRouter()
  const params = useParams()
  const [session, setSession] = useState<ReturnType<typeof getSession>>(null)
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    const s = getSession()
    if (!s || s.uuid !== params.uuid || !s.paid) {
      router.push('/')
      return
    }
    setSession(s)
    setIsLoaded(true)
  }, [params.uuid, router])

  const handleStartOver = () => {
    clearSession()
    router.push('/')
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
  const dailyFortunes = generateDailyFortune(lifePath, westernZodiac.sign)
  const luckyInfo = getLuckyInfo(lifePath, session.birthMonth)

  const scoreItems = [
    { label: '연애운', value: scores.love, icon: Heart, color: 'text-rose-500' },
    { label: '직장운', value: scores.career, icon: Briefcase, color: 'text-blue-500' },
    { label: '건강운', value: scores.health, icon: Activity, color: 'text-green-500' },
    { label: '재물운', value: scores.wealth, icon: Coins, color: 'text-amber-500' },
  ]

  return (
    <main className="min-h-screen bg-white">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="py-8 px-8 md:px-16 border-b border-border"
      >
        <div className="flex items-center justify-between">
          <h1 className="font-display text-lg tracking-widest uppercase">Fortune Studio</h1>
          <button
            onClick={handleStartOver}
            className="flex items-center gap-2 text-muted hover:text-primary transition-colors"
          >
            <RefreshCw size={14} strokeWidth={1.25} />
            <span className="text-xs tracking-widest uppercase hidden md:inline">다시 하기</span>
          </button>
        </div>
      </motion.header>

      {/* Success Banner */}
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        className="bg-black text-white py-4 px-8 text-center"
      >
        <div className="flex items-center justify-center gap-3">
          <Sparkles size={16} strokeWidth={1.25} />
          <span className="text-xs tracking-widest uppercase">
            프리미엄 운세가 잠금 해제되었습니다
          </span>
        </div>
      </motion.div>

      <div className="px-8 md:px-16 py-12 md:py-16 max-w-5xl mx-auto">
        {/* Birth Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <h2 className="font-display text-3xl md:text-5xl mb-4">
            {session.birthYear}년 {session.birthMonth}월 {session.birthDay}일
          </h2>
          <p className="text-muted">당신만을 위한 운세 리포트</p>
        </motion.div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {/* Chinese Zodiac */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="border border-border p-8"
          >
            <p className="text-xs tracking-widest uppercase text-muted mb-6">동양 띠</p>
            <div className="flex items-center gap-6 mb-6">
              <span className="text-7xl">{chineseZodiac.emoji}</span>
              <div>
                <h3 className="font-display text-3xl mb-1">{chineseZodiac.animal}띠</h3>
                <p className="text-sm text-muted">오행: {chineseZodiac.element}</p>
              </div>
            </div>
            <p className="text-muted leading-relaxed">{chineseZodiac.trait}</p>
          </motion.div>

          {/* Western Zodiac */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="border border-border p-8"
          >
            <p className="text-xs tracking-widest uppercase text-muted mb-6">서양 별자리</p>
            <div className="flex items-center gap-6 mb-6">
              <span className="text-7xl">{westernZodiac.emoji}</span>
              <div>
                <h3 className="font-display text-3xl mb-1">{westernZodiac.sign}</h3>
                <p className="text-sm text-muted">{westernZodiac.dates} · {westernZodiac.element}</p>
              </div>
            </div>
            <p className="text-muted leading-relaxed">
              수호성: {westernZodiac.ruling}<br />
              {westernZodiac.trait}
            </p>
          </motion.div>
        </div>

        {/* Life Path Number */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="border border-border p-8 md:p-12 mb-12"
        >
          <p className="text-xs tracking-widest uppercase text-muted mb-6">생명수 (수비학)</p>
          <div className="flex flex-col md:flex-row items-center gap-8">
            <div className="text-center">
              <span className="font-display text-8xl md:text-9xl">{lifePath}</span>
              <p className="text-lg font-display mt-2">{lifePathMeaning.title}</p>
            </div>
            <div className="flex-1">
              <p className="text-muted leading-relaxed mb-6">{lifePathMeaning.description}</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs tracking-widest uppercase text-muted mb-2">강점</p>
                  <div className="flex flex-wrap gap-2">
                    {lifePathMeaning.strengths.map((s, i) => (
                      <span key={i} className="text-xs px-3 py-1 bg-black/5 rounded-full">{s}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs tracking-widest uppercase text-muted mb-2">과제</p>
                  <div className="flex flex-wrap gap-2">
                    {lifePathMeaning.challenges.map((c, i) => (
                      <span key={i} className="text-xs px-3 py-1 bg-black/5 rounded-full">{c}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Fortune Scores */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12"
        >
          {scoreItems.map((item, index) => (
            <div key={item.label} className="border border-border p-6 text-center">
              <item.icon size={24} strokeWidth={1.25} className={`mx-auto mb-3 ${item.color}`} />
              <p className="font-display text-4xl mb-1">{item.value}%</p>
              <p className="text-xs tracking-widest uppercase text-muted">{item.label}</p>
              <div className="mt-3 h-1 bg-border rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${item.value}%` }}
                  transition={{ delay: 0.5 + index * 0.1, duration: 0.8 }}
                  className={`h-full ${item.color.replace('text-', 'bg-')}`}
                />
              </div>
            </div>
          ))}
        </motion.div>

        {/* Daily Fortune */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="border border-border p-8 mb-12"
        >
          <p className="text-xs tracking-widest uppercase text-muted mb-6">오늘의 운세</p>
          <div className="space-y-4">
            {dailyFortunes.map((fortune, i) => (
              <div key={i} className="flex gap-4">
                <span className="text-2xl">✦</span>
                <p className="text-muted leading-relaxed">{fortune}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Lucky Info */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="grid grid-cols-3 gap-4"
        >
          <div className="border border-border p-6 text-center">
            <p className="text-xs tracking-widest uppercase text-muted mb-3">행운의 색</p>
            <p className="font-display text-2xl">{luckyInfo.color}</p>
          </div>
          <div className="border border-border p-6 text-center">
            <p className="text-xs tracking-widest uppercase text-muted mb-3">행운의 숫자</p>
            <p className="font-display text-2xl">{luckyInfo.number}</p>
          </div>
          <div className="border border-border p-6 text-center">
            <p className="text-xs tracking-widest uppercase text-muted mb-3">행운의 방향</p>
            <p className="font-display text-2xl">{luckyInfo.direction}</p>
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="py-8 px-8 md:px-16 border-t border-border"
      >
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-[10px] tracking-widest uppercase text-muted">
            Fortune Studio를 이용해 주셔서 감사합니다
          </p>
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-muted hover:text-primary transition-colors"
          >
            <Home size={14} strokeWidth={1.25} />
            <span className="text-xs tracking-widest uppercase">홈으로</span>
          </button>
        </div>
      </motion.footer>
    </main>
  )
}
