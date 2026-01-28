'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Feather, Sparkles, PenTool } from 'lucide-react'
import { getOrCreateSession } from '@/lib/storage'

const LOADING_STEPS = [
  { text: 'Analyzing your name...', icon: Sparkles },
  { text: 'Selecting premium fonts...', icon: PenTool },
  { text: 'Crafting your signatures...', icon: Feather },
]

export default function LoadingPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    // Verify session exists
    const session = getOrCreateSession()
    if (!session || !session.name) {
      router.push('/')
      return
    }

    // Progress animation
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + 1
      })
    }, 30)

    // Step transitions
    const stepTimers = LOADING_STEPS.map((_, index) => {
      return setTimeout(() => {
        setCurrentStep(index)
      }, index * 1000)
    })

    // Redirect after loading
    const redirectTimer = setTimeout(() => {
      router.push('/preview')
    }, 3500)

    return () => {
      clearInterval(progressInterval)
      stepTimers.forEach(clearTimeout)
      clearTimeout(redirectTimer)
    }
  }, [router])

  const CurrentIcon = LOADING_STEPS[currentStep]?.icon || Sparkles

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-8">
      {/* Animated Logo */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
        className="mb-16"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          className="w-20 h-20 border border-border rounded-full flex items-center justify-center"
        >
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            transition={{ duration: 0.3 }}
          >
            <CurrentIcon size={28} strokeWidth={1} className="text-primary" />
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Loading Text */}
      <div className="text-center mb-12 h-16">
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
            transition={{ duration: 0.1 }}
          />
        </div>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-center mt-4 text-xs tracking-widest text-muted"
        >
          {progress}%
        </motion.p>
      </div>

      {/* Decorative Elements */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.1 }}
        transition={{ delay: 1, duration: 1 }}
        className="absolute inset-0 pointer-events-none overflow-hidden"
      >
        <div className="absolute top-1/4 left-1/4 w-96 h-96 border border-black/5 rounded-full" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 border border-black/5 rounded-full" />
      </motion.div>
    </main>
  )
}
