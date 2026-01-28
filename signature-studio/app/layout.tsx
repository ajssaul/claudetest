import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Signature.studio - AI Signature Generation",
  description: "Create your unique AI-generated signature",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        {/* Google Fonts - Direct Load */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500&family=Great+Vibes&family=Dancing+Script:wght@400;700&family=Alex+Brush&family=Pinyon+Script&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
