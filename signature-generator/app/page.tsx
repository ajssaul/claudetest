'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowRight, Sparkles } from 'lucide-react'
import { getOrCreateSession, createNewSession } from '@/lib/storage'

export default function HomePage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [isLoaded, setIsLoaded] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    // Check for existing paid session
    const session = getOrCreateSession()
    if (session?.paid) {
      router.push(`/results/${session.uuid}`)
      return
    }
    if (session?.name) {
      setName(session.name)
    }
    setIsLoaded(true)
  }, [router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || isSubmitting) return

    setIsSubmitting(true)
    createNewSession(name.trim())

    // Small delay for smooth transition
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
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="py-8 px-8 md:px-16"
      >
        <div className="flex items-center justify-between">
          <h1 className="font-display text-lg md:text-xl tracking-widest uppercase">
            Signature Studio
          </h1>
          <span className="text-xs tracking-ultra uppercase text-muted hidden md:block">
            Est. 2024
          </span>
        </div>
      </motion.header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-8 md:px-16 pb-24">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2, ease: 'easeOut' }}
          className="text-center max-w-2xl mx-auto mb-20"
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="inline-flex items-center gap-2 px-4 py-2 border border-border rounded-full mb-12"
          >
            <Sparkles size={14} strokeWidth={1.25} />
            <span className="text-xs tracking-widest uppercase">Premium Signatures</span>
          </motion.div>

          <h2 className="font-display text-4xl md:text-6xl lg:text-7xl leading-tight mb-8 tracking-tight">
            Your Name,
            <br />
            <span className="italic">Elegantly Crafted</span>
          </h2>

          <p className="font-body text-muted text-sm md:text-base leading-relaxed max-w-md mx-auto">
            Transform your name into a stunning, personalized signature.
            Curated from the world&apos;s most refined calligraphic styles.
          </p>
        </motion.div>

        {/* Input Form */}
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5, ease: 'easeOut' }}
          className="w-full max-w-md"
        >
          <div className="relative group">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              className="w-full bg-transparent border-b border-border py-6 text-center text-2xl md:text-3xl font-display tracking-wide focus:border-black transition-colors duration-500"
              maxLength={30}
              autoFocus
            />
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-px bg-black group-focus-within:w-full transition-all duration-500" />
          </div>

          <motion.button
            type="submit"
            disabled={!name.trim() || isSubmitting}
            whileHover={{ scale: name.trim() ? 1.02 : 1 }}
            whileTap={{ scale: name.trim() ? 0.98 : 1 }}
            className={`
              w-full mt-16 py-5 px-8
              flex items-center justify-center gap-3
              text-sm tracking-widest uppercase
              transition-all duration-500 btn-luxury
              ${name.trim()
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
                Creating...
              </span>
            ) : (
              <>
                Create My Signature
                <ArrowRight size={16} strokeWidth={1.25} />
              </>
            )}
          </motion.button>
        </motion.form>

        {/* Signature Preview Hint */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.2 }}
          className="mt-24 text-center"
        >
          <p className="signature-great-vibes text-4xl md:text-5xl text-light">
            {name || 'Your Signature'}
          </p>
          <p className="mt-4 text-xs tracking-widest uppercase text-muted">
            Live Preview
          </p>
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
          <span>Crafted with precision</span>
          <span>6 Premium Styles Available</span>
        </div>
      </motion.footer>
    </main>
  )
}
