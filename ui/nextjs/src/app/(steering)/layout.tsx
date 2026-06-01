// Steering layout — no EM sidebar, no dashboard chrome.
// Must NOT include <html>/<body> — only the root app layout may do that.
export default function SteeringLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb', fontFamily: 'Georgia, serif' }}>
      {children}
    </div>
  )
}
