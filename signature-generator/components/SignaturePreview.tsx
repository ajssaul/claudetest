'use client'

import { motion } from 'framer-motion'
import { Check } from 'lucide-react'
import { SignatureCanvas, SIGNATURE_STYLES } from './SignatureCanvas'

interface SignaturePreviewProps {
  name: string
  selectedId: number | null
  onSelect?: (id: number) => void
  blurred?: boolean
  showAll?: boolean
  animate?: boolean
}

export function SignaturePreview({
  name,
  selectedId,
  onSelect,
  blurred = false,
  showAll = true,
  animate = false
}: SignaturePreviewProps) {
  const styles = showAll ? SIGNATURE_STYLES : SIGNATURE_STYLES.slice(0, 4)

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
      {styles.map((style, index) => (
        <motion.div
          key={style.id}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1, duration: 0.6 }}
          onClick={() => onSelect?.(style.id)}
          className={`
            relative p-8 md:p-12 bg-white border transition-all duration-300 cursor-pointer
            ${selectedId === style.id
              ? 'border-black shadow-lg'
              : 'border-border hover:border-black/30'
            }
            ${blurred ? 'overflow-hidden' : ''}
          `}
        >
          {/* Selection Indicator */}
          {selectedId === style.id && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute top-4 right-4 w-6 h-6 bg-black rounded-full flex items-center justify-center"
            >
              <Check size={14} strokeWidth={2} className="text-white" />
            </motion.div>
          )}

          {/* Signature Display */}
          <div className={`text-center min-h-[80px] flex items-center justify-center ${blurred ? 'signature-blur' : ''}`}>
            <SignatureCanvas
              name={name}
              styleId={style.id}
              animate={animate}
              size="md"
            />
          </div>

          {/* Style Info */}
          <div className={`mt-8 pt-6 border-t border-border ${blurred ? '' : ''}`}>
            <p className="text-xs tracking-widest uppercase text-muted">
              {style.name}
            </p>
            <p className="text-[10px] tracking-wide text-light mt-1">
              {style.description}
            </p>
          </div>

          {/* Blur Overlay Gradient */}
          {blurred && (
            <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent pointer-events-none" />
          )}
        </motion.div>
      ))}
    </div>
  )
}

// Single signature card for results page
export function SignatureCard({
  name,
  styleId,
  isSelected = false,
  onClick
}: {
  name: string
  styleId: number
  isSelected?: boolean
  onClick?: () => void
}) {
  const style = SIGNATURE_STYLES[styleId]

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`
        relative p-8 bg-white border cursor-pointer transition-all duration-300
        ${isSelected ? 'border-black shadow-xl' : 'border-border hover:border-black/30'}
      `}
    >
      {isSelected && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute top-3 right-3 w-5 h-5 bg-black rounded-full flex items-center justify-center"
        >
          <Check size={12} strokeWidth={2} className="text-white" />
        </motion.div>
      )}

      <div className="text-center py-4">
        <SignatureCanvas name={name} styleId={styleId} animate={false} size="md" />
      </div>

      <p className="text-[10px] tracking-widest uppercase text-center text-muted mt-4">
        {style?.name}
      </p>
    </motion.div>
  )
}
