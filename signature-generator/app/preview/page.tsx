'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Lock, CreditCard, Shield, ArrowLeft, Check } from 'lucide-react'
import { getOrCreateSession, updateSession, markAsPaid } from '@/lib/storage'
import { SignaturePreview } from '@/components/SignaturePreview'

export default function PreviewPage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [selectedStyle, setSelectedStyle] = useState<number | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    const session = getOrCreateSession()
    if (!session || !session.name) {
      router.push('/')
      return
    }
    if (session.paid) {
      router.push(`/results/${session.uuid}`)
      return
    }
    setName(session.name)
    setIsLoaded(true)
  }, [router])

  const handleStyleSelect = (id: number) => {
    setSelectedStyle(id)
    updateSession({ selectedStyle: id })
  }

  const handlePayment = async () => {
    if (selectedStyle === null) return

    setIsProcessing(true)

    // Simulate payment processing
    await new Promise(resolve => setTimeout(resolve, 1500))

    // Mark as paid and get session
    const session = markAsPaid()

    if (session) {
      router.push(`/results/${session.uuid}`)
    }
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
          <h1 className="font-display text-lg tracking-widest uppercase">
            Signature Studio
          </h1>
          <div className="w-20" />
        </div>
      </motion.header>

      <div className="flex-1 px-8 md:px-16 py-12 md:py-20">
        {/* Title Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <h2 className="font-display text-3xl md:text-4xl mb-4">
            Your Signatures Are Ready
          </h2>
          <p className="text-sm text-muted tracking-wide">
            Select your preferred style to unlock the high-resolution version
          </p>
        </motion.div>

        {/* Signature Previews with Blur */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="max-w-4xl mx-auto mb-16"
        >
          <SignaturePreview
            name={name}
            selectedId={selectedStyle}
            onSelect={handleStyleSelect}
            blurred={true}
            showAll={false}
            animate={false}
          />

          {/* More Styles Note */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="text-center text-xs tracking-widest uppercase text-muted mt-8"
          >
            + 2 More Premium Styles Included
          </motion.p>
        </motion.div>

        {/* Payment Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="max-w-md mx-auto"
        >
          {/* Price Card */}
          <div className="bg-white border border-border p-8 md:p-12 text-center mb-8">
            <p className="text-xs tracking-widest uppercase text-muted mb-4">
              Premium Package
            </p>
            <div className="flex items-baseline justify-center gap-1 mb-2">
              <span className="font-display text-5xl">$9</span>
              <span className="text-muted text-sm">.99</span>
            </div>
            <p className="text-xs text-muted mb-8">One-time payment</p>

            {/* Features */}
            <div className="space-y-3 text-left mb-8">
              {[
                '6 Premium Signature Styles',
                'High-Resolution PNG Downloads',
                'Transparent Background',
                'Commercial Use License',
                'Instant Access Forever'
              ].map((feature, i) => (
                <div key={i} className="flex items-center gap-3">
                  <Check size={14} strokeWidth={1.5} className="text-primary" />
                  <span className="text-sm text-muted">{feature}</span>
                </div>
              ))}
            </div>

            {/* Payment Button */}
            <motion.button
              onClick={handlePayment}
              disabled={selectedStyle === null || isProcessing}
              whileHover={{ scale: selectedStyle !== null && !isProcessing ? 1.02 : 1 }}
              whileTap={{ scale: selectedStyle !== null && !isProcessing ? 0.98 : 1 }}
              className={`
                w-full py-5 flex items-center justify-center gap-3
                text-sm tracking-widest uppercase transition-all btn-luxury
                ${selectedStyle !== null && !isProcessing
                  ? 'bg-black text-white cursor-pointer'
                  : 'bg-border text-muted cursor-not-allowed'
                }
              `}
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
                    Secure Payment Processing...
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
                    {selectedStyle !== null ? 'Unlock My Signatures' : 'Select a Style First'}
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>
          </div>

          {/* Trust Badges */}
          <div className="flex items-center justify-center gap-8 text-muted">
            <div className="flex items-center gap-2">
              <Shield size={14} strokeWidth={1.25} />
              <span className="text-[10px] tracking-widest uppercase">Secure</span>
            </div>
            <div className="flex items-center gap-2">
              <Lock size={14} strokeWidth={1.25} />
              <span className="text-[10px] tracking-widest uppercase">Encrypted</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <footer className="py-6 px-8 md:px-16 border-t border-border">
        <p className="text-center text-[10px] tracking-widest uppercase text-light">
          Demo Mode — No Real Payment Required
        </p>
      </footer>
    </main>
  )
}
