import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Fortune Studio | Discover Your Destiny',
  description: 'Unlock the secrets of your birth date with premium fortune readings.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-background antialiased">
        {children}
      </body>
    </html>
  )
}
