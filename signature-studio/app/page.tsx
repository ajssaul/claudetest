'use client';

import { useState } from 'react';
import { ArrowRight, Menu } from 'lucide-react';

export default function Home() {
  const [name, setName] = useState('');

  // Test signatures with different fonts
  const testSignatures = [
    { font: 'signature-great-vibes', label: 'Great Vibes' },
    { font: 'signature-dancing-script', label: 'Dancing Script' },
    { font: 'signature-alex-brush', label: 'Alex Brush' },
    { font: 'signature-pinyon-script', label: 'Pinyon Script' },
  ];

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <header className="w-full px-8 py-6 flex items-center justify-between">
        <div className="font-bold text-xl">Signature.studio</div>
        <button className="p-2 hover:bg-gray-50 rounded-full transition">
          <Menu size={24} strokeWidth={1.25} />
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center px-8 pb-32">
        <div className="w-full max-w-2xl mx-auto text-center space-y-16">
          {/* Headline */}
          <h1 className="text-6xl md:text-7xl lg:text-8xl leading-tight">
            Find your signature style
          </h1>

          {/* Input */}
          <div className="space-y-12">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              className="w-full text-center text-xl md:text-2xl bg-transparent border-0 border-b border-gray-300 pb-4 px-4 focus:outline-none focus:border-black transition"
              autoFocus
            />

            {/* Test Signatures */}
            {name && (
              <div className="space-y-8 pt-8">
                <p className="text-sm text-gray-500">Preview (폰트 테스트)</p>
                {testSignatures.map((sig, index) => (
                  <div
                    key={index}
                    className="p-6 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <p className="text-xs text-gray-400 mb-2">{sig.label}</p>
                    <div className={`${sig.font} text-5xl`}>
                      {name}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <button
              disabled={!name.trim()}
              className="group mx-auto flex items-center gap-3 px-8 py-4 bg-black text-white rounded-full hover:bg-gray-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span>Start Design</span>
              <ArrowRight size={20} strokeWidth={1.5} className="group-hover:translate-x-1 transition" />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
