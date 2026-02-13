'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Moon, Star, Sparkles, Sun } from 'lucide-react'
import { getSession } from '@/lib/storage'

const LOADING_STEPS = [
  { text: '생년월일 분석 중...', icon: Moon },
  { text: '별자리 확인 중...', icon: Star },
  { text: '띠 해석 중...', icon: Sun },
  { text: '운세 생성 중...', icon: Sparkles },
]

export default function LoadingPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const session = getSession()
    if (!session) {
      router.push('/')
      return
    }

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + 1
      })
    }, 35)

    const stepTimers = LOADING_STEPS.map((_, index) => {
      return setTimeout(() => setCurrentStep(index), index * 900)
    })

    const redirectTimer = setTimeout(() => {
      router.push(`/results/${session.uuid}`)
    }, 4000)

    return () => {
      clearInterval(progressInterval)
      stepTimers.forEach(clearTimeout)
      clearTimeout(redirectTimer)
    }
  }, [router])

  const CurrentIcon = LOADING_STEPS[currentStep]?.icon || Moon

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-8 bg-white">
      {/* Animated Symbol */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="mb-16"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          className="w-24 h-24 border border-border rounded-full flex items-center justify-center relative"
        >
          {/* Orbiting dots */}
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 bg-black rounded-full"
              animate={{
                rotate: 360,
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: 'linear',
                delay: i * 1,
              }}
              style={{
                transformOrigin: '12px 12px',
                top: '50%',
                left: '50%',
                marginTop: '-4px',
                marginLeft: '-4px',
              }}
            />
          ))}

          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.5 }}
              transition={{ duration: 0.3 }}
            >
              <CurrentIcon size={32} strokeWidth={1} className="text-primary" />
            </motion.div>
          </AnimatePresence>
        </motion.div>
      </motion.div>

      {/* Loading Text */}
      <div className="text-center mb-12 h-12">
        <AnimatePresence mode="wait">
          <motion.p
            key={currentStep}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
            className="font-display text-xl md:text-2xl tracking-wide"
          >
            {LOADING_STEPS[currentStep]?.text}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* Progress Bar */}
      <div className="w-full max-w-xs">
        <div className="h-px bg-border overflow-hidden">
          <motion.div
            className="h-full bg-primary"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-center mt-4 text-xs tracking-widest text-muted">
          {progress}%
        </p>
      </div>

      {/* Zodiac Circle */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.1 }}
        transition={{ delay: 0.5, duration: 1 }}
        className="absolute inset-0 flex items-center justify-center pointer-events-none text-6xl"
      >
        <div className="grid grid-cols-4 gap-8 opacity-30">
          {['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'].map((sign, i) => (
            <motion.span
              key={i}
              animate={{ opacity: [0.3, 0.6, 0.3] }}
              transition={{ duration: 2, repeat: Infinity, delay: i * 0.1 }}
            >
              {sign}
            </motion.span>
          ))}
        </div>
      </motion.div>
    </main>
  )
}
