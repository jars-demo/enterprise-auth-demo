import Link from 'next/link'

import { BackToTop } from './BackToTop'

export const REPO_URL = 'https://github.com/jars-demo/enterprise-auth-demo'

export function Mark({ size = 22 }: { size?: number }) {
  // A shield with a keyhole: identity, checked.
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <rect x="1" y="1" width="22" height="22" rx="6" fill="#0f766e" />
      <path
        d="M12 4.5 6.5 6.6v4.6c0 3.6 2.3 6.4 5.5 7.8 3.2-1.4 5.5-4.2 5.5-7.8V6.6z"
        fill="#ffffff"
      />
      <circle cx="12" cy="10.6" r="1.6" fill="#0f766e" />
      <path d="M11.2 11.6h1.6l.4 3h-2.4z" fill="#0f766e" />
    </svg>
  )
}

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="border-b border-line">
        <nav
          aria-label="Main"
          className="mx-auto flex h-14 max-w-5xl items-center justify-between gap-4 px-4"
        >
          <Link href="/" className="inline-flex items-center gap-2.5 text-[15px] font-semibold">
            <Mark />
            Enterprise auth, hands on
          </Link>
          <ul className="flex items-center gap-5 text-[14px] text-ink-2">
            <li>
              <Link href="/workshop" className="hover:text-ink">
                Workshop
              </Link>
            </li>
            <li>
              <a href={REPO_URL} className="hover:text-ink">
                GitHub
              </a>
            </li>
          </ul>
        </nav>
      </header>
      <main id="main" className="flex-1">
        {children}
      </main>
      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-6 text-[13px] text-muted sm:flex-row sm:justify-between">
          <span>Enterprise auth, hands on · MIT licensed</span>
          <a href={REPO_URL} className="hover:text-ink">
            GitHub
          </a>
        </div>
      </footer>
      <BackToTop />
    </>
  )
}
