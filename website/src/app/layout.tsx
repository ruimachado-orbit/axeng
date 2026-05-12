import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Axeng — Engineering OS',
  description: 'Autonomous AI chief of staff for engineering leaders',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}
