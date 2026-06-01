// Steering layout — no EM sidebar, no dashboard chrome.
// This is the CEO's document view: clean, full-width, print-friendly.
export default function SteeringLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0, background: '#f9fafb', fontFamily: 'Georgia, serif' }}>
        {children}
      </body>
    </html>
  )
}
