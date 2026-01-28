'use client';

import { useState } from 'react';
import { ArrowRight, Menu } from 'lucide-react';

interface HeroSectionProps {
  onStartDesign: (name: string) => void;
}

export default function HeroSection({ onStartDesign }: HeroSectionProps) {
  const [name, setName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      onStartDesign(name.trim());
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <header className="w-full px-8 py-6 flex items-center justify-between">
        <div className="font-bold text-xl tracking-tight">
          Signature.studio
        </div>
        <button
          className="p-2 hover:bg-gray-50 rounded-full transition-colors"
          aria-label="Menu"
        >
          <Menu size={24} strokeWidth={1.25} />
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center px-8 pb-32">
        <div className="w-full max-w-2xl mx-auto text-center space-y-16">
          {/* Headline */}
          <h1 className="text-6xl md:text-7xl lg:text-8xl font-serif font-normal leading-tight tracking-tight">
            Find your signature style
          </h1>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="space-y-12">
            <div className="relative">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your name"
                className="w-full text-center text-xl md:text-2xl font-light tracking-wide bg-transparent border-0 border-b border-gray-300 pb-4 px-4 focus:outline-none focus:border-black transition-colors placeholder:text-gray-400"
                autoFocus
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!name.trim()}
              className="group mx-auto flex items-center gap-3 px-8 py-4 bg-black text-white rounded-full hover:bg-gray-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-black"
            >
              <span className="text-base font-normal tracking-wide">
                Start Design
              </span>
              <ArrowRight
                size={20}
                strokeWidth={1.5}
                className="group-hover:translate-x-1 transition-transform"
              />
            </button>
          </form>
        </div>
      </main>

      {/* Footer Spacing */}
      <div className="h-16" />
    </div>
  );
}
