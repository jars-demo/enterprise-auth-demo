'use client'

import { useSyncExternalStore } from 'react'

// A small button that appears after scrolling down and returns to the top.

function subscribe(onChange: () => void) {
  window.addEventListener('scroll', onChange, { passive: true })
  return () => window.removeEventListener('scroll', onChange)
}

export function BackToTop() {
  const visible = useSyncExternalStore(
    subscribe,
    () => window.scrollY > 600,
    () => false,
  )
  return (
    <button
      type="button"
      aria-label="Back to top"
      aria-hidden={!visible}
      tabIndex={visible ? 0 : -1}
      onClick={() => {
        const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
        window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' })
      }}
      className={`fixed right-4 bottom-[max(1rem,env(safe-area-inset-bottom))] z-40 grid size-10 place-items-center rounded-md border border-line-strong bg-canvas text-ink-2 shadow-sm transition-opacity duration-200 hover:text-ink ${
        visible ? 'opacity-100' : 'pointer-events-none opacity-0'
      }`}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M12 19V5M5 12l7-7 7 7"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </button>
  )
}
