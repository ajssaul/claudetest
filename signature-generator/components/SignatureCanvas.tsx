'use client'

import { useRef, useEffect, useState } from 'react'
import { motion, useAnimation, type Variants } from 'framer-motion'

export interface SignatureStyle {
  id: number
  name: string
  fontFamily: string
  className: string
  description: string
}

export const SIGNATURE_STYLES: SignatureStyle[] = [
  {
    id: 0,
    name: 'Classic Elegance',
    fontFamily: 'Great Vibes',
    className: 'signature-great-vibes',
    description: 'Timeless flowing script'
  },
  {
    id: 1,
    name: 'Royal Script',
    fontFamily: 'Pinyon Script',
    className: 'signature-pinyon',
    description: 'Sophisticated formal style'
  },
  {
    id: 2,
    name: 'Modern Brush',
    fontFamily: 'Alex Brush',
    className: 'signature-alex-brush',
    description: 'Contemporary brushwork'
  },
  {
    id: 3,
    name: 'Artistic Flow',
    fontFamily: 'Dancing Script',
    className: 'signature-dancing',
    description: 'Dynamic artistic expression'
  },
  {
    id: 4,
    name: 'Refined Grace',
    fontFamily: 'Allura',
    className: 'signature-allura',
    description: 'Delicate refined curves'
  },
  {
    id: 5,
    name: 'Casual Chic',
    fontFamily: 'Sacramento',
    className: 'signature-sacramento',
    description: 'Effortlessly stylish'
  }
]

interface SignatureCanvasProps {
  name: string
  styleId: number
  animate?: boolean
  blur?: boolean
  showWatermark?: boolean
  size?: 'sm' | 'md' | 'lg'
  onAnimationComplete?: () => void
}

export function SignatureCanvas({
  name,
  styleId,
  animate = true,
  blur = false,
  showWatermark = false,
  size = 'md',
  onAnimationComplete
}: SignatureCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const controls = useAnimation()
  const [isVisible, setIsVisible] = useState(false)

  const style = SIGNATURE_STYLES[styleId] || SIGNATURE_STYLES[0]

  const sizeClasses = {
    sm: 'text-3xl md:text-4xl',
    md: 'text-4xl md:text-6xl',
    lg: 'text-5xl md:text-7xl lg:text-8xl'
  }

  useEffect(() => {
    if (animate) {
      setIsVisible(false)
      const timer = setTimeout(() => {
        setIsVisible(true)
        controls.start({
          opacity: 1,
          pathLength: 1,
          transition: { duration: 2, ease: 'easeOut' }
        })
      }, 100)
      return () => clearTimeout(timer)
    } else {
      setIsVisible(true)
    }
  }, [animate, name, styleId, controls])

  const pathVariants: Variants = {
    hidden: {
      opacity: 0,
      pathLength: 0,
    },
    visible: {
      opacity: 1,
      pathLength: 1,
      transition: {
        duration: 2.5,
        ease: [0.4, 0, 0.2, 1],
        opacity: { duration: 0.3 }
      }
    }
  }

  const letterVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i: number) => ({
      opacity: 1,
      y: 0,
      transition: {
        delay: i * 0.05,
        duration: 0.5,
        ease: [0.4, 0, 0.2, 1]
      }
    })
  }

  return (
    <div
      ref={containerRef}
      className={`relative inline-block ${blur ? 'signature-blur' : ''}`}
    >
      {/* Main Signature Text */}
      <div className={`${style.className} ${sizeClasses[size]} text-primary select-none`}>
        {animate ? (
          <motion.span
            initial="hidden"
            animate={isVisible ? 'visible' : 'hidden'}
            onAnimationComplete={onAnimationComplete}
            className="inline-block"
          >
            {name.split('').map((char, i) => (
              <motion.span
                key={`${char}-${i}`}
                custom={i}
                variants={letterVariants}
                className="inline-block"
                style={{ whiteSpace: char === ' ' ? 'pre' : 'normal' }}
              >
                {char}
              </motion.span>
            ))}
          </motion.span>
        ) : (
          <span>{name}</span>
        )}
      </div>

      {/* Decorative Underline SVG */}
      {animate && isVisible && (
        <motion.svg
          className="absolute -bottom-2 left-0 w-full h-4 overflow-visible"
          viewBox="0 0 200 20"
          preserveAspectRatio="none"
        >
          <motion.path
            d="M0,10 Q50,0 100,10 T200,10"
            fill="none"
            stroke="currentColor"
            strokeWidth="0.5"
            strokeLinecap="round"
            variants={pathVariants}
            initial="hidden"
            animate="visible"
            style={{ opacity: 0.3 }}
          />
        </motion.svg>
      )}

      {/* Watermark */}
      {showWatermark && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-xs tracking-widest uppercase text-black/10 rotate-[-15deg]">
            SIGNATURE STUDIO
          </div>
        </div>
      )}
    </div>
  )
}

// Export component for PNG conversion
export function SignatureForExport({
  name,
  styleId,
  size = 'lg'
}: {
  name: string
  styleId: number
  size?: 'sm' | 'md' | 'lg'
}) {
  const style = SIGNATURE_STYLES[styleId] || SIGNATURE_STYLES[0]

  const sizeClasses = {
    sm: 'text-4xl',
    md: 'text-6xl',
    lg: 'text-8xl'
  }

  return (
    <div
      className={`${style.className} ${sizeClasses[size]} text-primary p-8`}
      style={{ background: 'transparent' }}
    >
      {name}
    </div>
  )
}
