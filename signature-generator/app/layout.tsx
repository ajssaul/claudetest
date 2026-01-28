import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Signature Studio | Luxury Digital Signatures',
  description: 'Create elegant, personalized digital signatures with our premium signature generator.',
  keywords: ['signature', 'digital signature', 'elegant', 'personalized', 'luxury'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background antialiased">
        {children}
      </body>
    </html>
  )
}
