'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { RefreshCw, Home, Heart, Briefcase, Activity, Coins, Clock, AlertTriangle, Gift, Compass } from 'lucide-react'
import { getSession, clearSession } from '@/lib/storage'
import {
  getChineseZodiac,
  getWesternZodiac,
  getLifePathNumber,
  LIFE_PATH_MEANINGS,
  getCompatibilityScore,
  getLuckyInfo
} from '@/lib/fortune'

interface DailyFortune {
  general: string
  love: string
  career: string
  health: string
  luckyTime: string
  luckyItem: string
  warning: string
}

export default function ResultsPage() {
  const router = useRouter()
  const params = useParams()
  const [session, setSession] = useState<ReturnType<typeof getSession>>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const [dailyFortune, setDailyFortune] = useState<DailyFortune | null>(null)
  const [isLoadingFortune, setIsLoadingFortune] = useState(true)

  useEffect(() => {
    const s = getSession()
    if (!s || s.uuid !== params.uuid) {
      router.push('/')
      return
    }
    setSession(s)
    setIsLoaded(true)

    // API에서 오늘의 운세 가져오기
    fetchDailyFortune(s)
  }, [params.uuid, router])

  const fetchDailyFortune = async (s: NonNullable<ReturnType<typeof getSession>>) => {
    try {
      const westernZodiac = getWesternZodiac(s.birthMonth, s.birthDay)
      const signMap: Record<string, string> = {
        '양자리': 'aries', '황소자리': 'taurus', '쌍둥이자리': 'gemini',
        '게자리': 'cancer', '사자자리': 'leo', '처녀자리': 'virgo',
        '천칭자리': 'libra', '전갈자리': 'scorpio', '사수자리': 'sagittarius',
        '염소자리': 'capricorn', '물병자리': 'aquarius', '물고기자리': 'pisces'
      }
      const sign = signMap[westernZodiac.sign] || 'aries'

      const response = await fetch('/api/horoscope', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sign,
          birthYear: s.birthYear,
          birthMonth: s.birthMonth,
          birthDay: s.birthDay,
        }),
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          setDailyFortune(result.data)
        }
      }
    } catch (error) {
      console.error('Failed to fetch fortune:', error)
    } finally {
      setIsLoadingFortune(false)
    }
  }

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
  const luckyInfo = getLuckyInfo(lifePath, session.birthMonth)

  const scoreItems = [
    { label: '연애운', value: scores.love, icon: Heart, color: 'text-rose-500', bg: 'bg-rose-500' },
    { label: '직장운', value: scores.career, icon: Briefcase, color: 'text-blue-500', bg: 'bg-blue-500' },
    { label: '건강운', value: scores.health, icon: Activity, color: 'text-green-500', bg: 'bg-green-500' },
    { label: '재물운', value: scores.wealth, icon: Coins, color: 'text-amber-500', bg: 'bg-amber-500' },
  ]

  const today = new Date()
  const dateString = `${today.getFullYear()}년 ${today.getMonth() + 1}월 ${today.getDate()}일`

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

      <div className="px-8 md:px-16 py-12 md:py-16 max-w-5xl mx-auto">
        {/* Birth Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <p className="text-xs tracking-widest uppercase text-muted mb-4">{dateString} 운세</p>
          <h2 className="font-display text-3xl md:text-5xl mb-2">
            {session.birthYear}년 {session.birthMonth}월 {session.birthDay}일생
          </h2>
          <p className="text-muted">
            {chineseZodiac.animal}띠 · {westernZodiac.sign} · 생명수 {lifePath}
          </p>
        </motion.div>

        {/* 오늘의 운세 - 메인 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="border-2 border-black p-8 md:p-12 mb-8"
        >
          <h3 className="font-display text-2xl mb-6 text-center">오늘의 운세</h3>
          {isLoadingFortune ? (
            <div className="flex justify-center py-8">
              <div className="w-6 h-6 border border-black/20 rounded-full border-t-black animate-spin" />
            </div>
          ) : dailyFortune ? (
            <div className="space-y-6">
              <p className="text-lg leading-relaxed text-center">{dailyFortune.general}</p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t border-border">
                <div className="flex items-start gap-3">
                  <Clock size={18} className="text-muted mt-1 flex-shrink-0" />
                  <div>
                    <p className="text-xs tracking-widest uppercase text-muted mb-1">행운의 시간</p>
                    <p className="font-display text-lg">{dailyFortune.luckyTime}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Gift size={18} className="text-muted mt-1 flex-shrink-0" />
                  <div>
                    <p className="text-xs tracking-widest uppercase text-muted mb-1">행운의 아이템</p>
                    <p className="font-display text-lg">{dailyFortune.luckyItem}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <AlertTriangle size={18} className="text-amber-500 mt-1 flex-shrink-0" />
                  <div>
                    <p className="text-xs tracking-widest uppercase text-muted mb-1">주의사항</p>
                    <p className="font-display text-lg">{dailyFortune.warning}</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-center text-muted">운세를 불러오지 못했습니다.</p>
          )}
        </motion.div>

        {/* 카테고리별 운세 */}
        {dailyFortune && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12"
          >
            <div className="border border-border p-6">
              <div className="flex items-center gap-2 mb-4">
                <Heart size={18} className="text-rose-500" />
                <p className="text-xs tracking-widest uppercase">연애운</p>
              </div>
              <p className="text-muted leading-relaxed">{dailyFortune.love}</p>
            </div>
            <div className="border border-border p-6">
              <div className="flex items-center gap-2 mb-4">
                <Briefcase size={18} className="text-blue-500" />
                <p className="text-xs tracking-widest uppercase">직장운</p>
              </div>
              <p className="text-muted leading-relaxed">{dailyFortune.career}</p>
            </div>
            <div className="border border-border p-6">
              <div className="flex items-center gap-2 mb-4">
                <Activity size={18} className="text-green-500" />
                <p className="text-xs tracking-widest uppercase">건강운</p>
              </div>
              <p className="text-muted leading-relaxed">{dailyFortune.health}</p>
            </div>
          </motion.div>
        )}

        {/* Fortune Scores */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
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
                  className={`h-full ${item.bg}`}
                />
              </div>
            </div>
          ))}
        </motion.div>

        {/* 띠 & 별자리 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {/* Chinese Zodiac */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
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
            transition={{ delay: 0.5 }}
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
          transition={{ delay: 0.6 }}
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

        {/* Lucky Info */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="grid grid-cols-3 gap-4"
        >
          <div className="border border-border p-6 text-center">
            <div className="w-10 h-10 rounded-full bg-black/5 flex items-center justify-center mx-auto mb-3">
              <div className="w-4 h-4 rounded-full" style={{ backgroundColor: luckyInfo.color === '빨강' ? '#ef4444' : luckyInfo.color === '파랑' ? '#3b82f6' : luckyInfo.color === '노랑' ? '#eab308' : luckyInfo.color === '초록' ? '#22c55e' : luckyInfo.color === '보라' ? '#a855f7' : luckyInfo.color === '주황' ? '#f97316' : luckyInfo.color === '금색' ? '#d4af37' : luckyInfo.color === '흰색' ? '#f5f5f5' : '#000000' }} />
            </div>
            <p className="text-xs tracking-widest uppercase text-muted mb-2">행운의 색</p>
            <p className="font-display text-xl">{luckyInfo.color}</p>
          </div>
          <div className="border border-border p-6 text-center">
            <div className="w-10 h-10 rounded-full bg-black/5 flex items-center justify-center mx-auto mb-3 font-display text-lg">
              {luckyInfo.number}
            </div>
            <p className="text-xs tracking-widest uppercase text-muted mb-2">행운의 숫자</p>
            <p className="font-display text-xl">{luckyInfo.number}</p>
          </div>
          <div className="border border-border p-6 text-center">
            <div className="w-10 h-10 rounded-full bg-black/5 flex items-center justify-center mx-auto mb-3">
              <Compass size={18} />
            </div>
            <p className="text-xs tracking-widest uppercase text-muted mb-2">행운의 방향</p>
            <p className="font-display text-xl">{luckyInfo.direction}</p>
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="py-8 px-8 md:px-16 border-t border-border"
      >
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-[10px] tracking-widest uppercase text-muted">
            Fortune Studio · {dateString}
          </p>
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-muted hover:text-primary transition-colors"
          >
            <Home size={14} strokeWidth={1.25} />
            <span className="text-xs tracking-widest uppercase">다른 생년월일로 보기</span>
          </button>
        </div>
      </motion.footer>
    </main>
  )
}
