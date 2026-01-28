'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import HeroSection from './components/HeroSection';
import ProcessingSection from './components/ProcessingSection';
import PaywallSection from './components/PaywallSection';
import ResultSection from './components/ResultSection';

type AppState = 'hero' | 'processing' | 'paywall' | 'result';

export default function Home() {
  const [currentState, setCurrentState] = useState<AppState>('hero');
  const [userName, setUserName] = useState('');

  const handleStartDesign = (name: string) => {
    setUserName(name);
    setCurrentState('processing');
  };

  const handleProcessingComplete = () => {
    setCurrentState('paywall');
  };

  const handlePaymentComplete = () => {
    setCurrentState('result');
  };

  // Animation variants for page transitions
  const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  };

  const pageTransition = {
    type: 'tween',
    ease: 'easeInOut',
    duration: 0.5,
  };

  return (
    <AnimatePresence mode="wait">
      {currentState === 'hero' && (
        <motion.div
          key="hero"
          variants={pageVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={pageTransition}
        >
          <HeroSection onStartDesign={handleStartDesign} />
        </motion.div>
      )}

      {currentState === 'processing' && (
        <motion.div
          key="processing"
          variants={pageVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={pageTransition}
        >
          <ProcessingSection name={userName} onComplete={handleProcessingComplete} />
        </motion.div>
      )}

      {currentState === 'paywall' && (
        <motion.div
          key="paywall"
          variants={pageVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={pageTransition}
        >
          <PaywallSection name={userName} onPaymentComplete={handlePaymentComplete} />
        </motion.div>
      )}

      {currentState === 'result' && (
        <motion.div
          key="result"
          variants={pageVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={pageTransition}
        >
          <ResultSection name={userName} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
