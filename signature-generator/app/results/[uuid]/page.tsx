'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Download, Check, RefreshCw, Home, Sparkles } from 'lucide-react'
import { toPng } from 'html-to-image'
import { getOrCreateSession, clearSession } from '@/lib/storage'
import { SignatureCanvas, SIGNATURE_STYLES, SignatureForExport } from '@/components/SignatureCanvas'

export default function ResultsPage() {
  const router = useRouter()
  const params = useParams()
  const [name, setName] = useState('')
  const [selectedStyle, setSelectedStyle] = useState(0)
  const [isLoaded, setIsLoaded] = useState(false)
  const [downloading, setDownloading] = useState<number | null>(null)
  const [downloadComplete, setDownloadComplete] = useState<number[]>([])
  const exportRefs = useRef<(HTMLDivElement | null)[]>([])

  useEffect(() => {
    const session = getOrCreateSession()

    // Verify session matches URL and is paid
    if (!session || session.uuid !== params.uuid || !session.paid) {
      router.push('/')
      return
    }

    setName(session.name)
    setSelectedStyle(session.selectedStyle || 0)
    setIsLoaded(true)
  }, [params.uuid, router])

  const handleDownload = async (styleId: number) => {
    const element = exportRefs.current[styleId]
    if (!element || downloading !== null) return

    setDownloading(styleId)

    try {
      const dataUrl = await toPng(element, {
        backgroundColor: undefined,
        pixelRatio: 3,
        quality: 1,
      })

      const link = document.createElement('a')
      link.download = `signature-${name.toLowerCase().replace(/\s+/g, '-')}-${SIGNATURE_STYLES[styleId].name.toLowerCase().replace(/\s+/g, '-')}.png`
      link.href = dataUrl
      link.click()

      setDownloadComplete(prev => [...prev, styleId])
    } catch (err) {
      console.error('Download failed:', err)
    } finally {
      setDownloading(null)
    }
  }

  const handleDownloadAll = async () => {
    for (let i = 0; i < SIGNATURE_STYLES.length; i++) {
      await handleDownload(i)
      await new Promise(resolve => setTimeout(resolve, 500))
    }
  }

  const handleStartOver = () => {
    clearSession()
    router.push('/')
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
    <main className="min-h-screen flex flex-col bg-white">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="py-8 px-8 md:px-16 border-b border-border"
      >
        <div className="flex items-center justify-between">
          <h1 className="font-display text-lg tracking-widest uppercase">
            Signature Studio
          </h1>
          <button
            onClick={handleStartOver}
            className="flex items-center gap-2 text-muted hover:text-primary transition-colors"
          >
            <RefreshCw size={14} strokeWidth={1.25} />
            <span className="text-xs tracking-widest uppercase hidden md:inline">Start Over</span>
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
            Payment Successful — Your Premium Signatures Are Ready
          </span>
        </div>
      </motion.div>

      <div className="flex-1 px-8 md:px-16 py-12 md:py-20">
        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <h2 className="font-display text-3xl md:text-5xl mb-4">
            Welcome, <span className="italic">{name}</span>
          </h2>
          <p className="text-sm text-muted tracking-wide">
            Your personalized signature collection is ready for download
          </p>
        </motion.div>

        {/* Download All Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-center mb-16"
        >
          <motion.button
            onClick={handleDownloadAll}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            disabled={downloading !== null}
            className="inline-flex items-center gap-3 bg-black text-white py-4 px-8 text-xs tracking-widest uppercase btn-luxury"
          >
            <Download size={14} strokeWidth={1.25} />
            Download All Signatures
          </motion.button>
        </motion.div>

        {/* Signature Grid */}
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {SIGNATURE_STYLES.map((style, index) => (
            <motion.div
              key={style.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * index }}
              className={`
                relative bg-white border p-8 transition-all duration-300
                ${selectedStyle === style.id ? 'border-black shadow-lg' : 'border-border hover:border-black/30'}
              `}
            >
              {/* Recommended Badge */}
              {selectedStyle === style.id && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-black text-white px-3 py-1 text-[10px] tracking-widest uppercase">
                  Your Selection
                </div>
              )}

              {/* Signature Display */}
              <div className="text-center py-8 min-h-[120px] flex items-center justify-center">
                <SignatureCanvas
                  name={name}
                  styleId={style.id}
                  animate={false}
                  size="md"
                />
              </div>

              {/* Style Info */}
              <div className="border-t border-border pt-6 mt-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-xs tracking-widest uppercase">{style.name}</p>
                    <p className="text-[10px] text-muted mt-1">{style.description}</p>
                  </div>
                </div>

                {/* Download Button */}
                <motion.button
                  onClick={() => handleDownload(style.id)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  disabled={downloading !== null}
                  className={`
                    w-full py-3 flex items-center justify-center gap-2
                    text-[10px] tracking-widest uppercase border transition-all
                    ${downloadComplete.includes(style.id)
                      ? 'bg-black text-white border-black'
                      : 'border-border hover:border-black hover:bg-black hover:text-white'
                    }
                  `}
                >
                  <AnimatePresence mode="wait">
                    {downloading === style.id ? (
                      <motion.span
                        key="downloading"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex items-center gap-2"
                      >
                        <motion.span
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                          className="w-3 h-3 border border-current border-t-transparent rounded-full"
                        />
                        Processing...
                      </motion.span>
                    ) : downloadComplete.includes(style.id) ? (
                      <motion.span
                        key="complete"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex items-center gap-2"
                      >
                        <Check size={12} strokeWidth={1.5} />
                        Downloaded
                      </motion.span>
                    ) : (
                      <motion.span
                        key="download"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex items-center gap-2"
                      >
                        <Download size={12} strokeWidth={1.5} />
                        Download PNG
                      </motion.span>
                    )}
                  </AnimatePresence>
                </motion.button>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Hidden Export Elements for PNG Generation */}
        <div className="fixed -left-[9999px] top-0 pointer-events-none">
          {SIGNATURE_STYLES.map((style, index) => (
            <div
              key={style.id}
              ref={el => { exportRefs.current[index] = el }}
              className="inline-block"
            >
              <SignatureForExport name={name} styleId={style.id} size="lg" />
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="py-8 px-8 md:px-16 border-t border-border"
      >
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-[10px] tracking-widest uppercase text-muted">
            Thank you for choosing Signature Studio
          </p>
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-muted hover:text-primary transition-colors"
          >
            <Home size={14} strokeWidth={1.25} />
            <span className="text-xs tracking-widest uppercase">Return Home</span>
          </button>
        </div>
      </motion.footer>
    </main>
  )
}
