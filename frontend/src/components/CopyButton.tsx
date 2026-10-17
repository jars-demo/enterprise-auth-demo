'use client'

import { useState } from 'react'

export function CopyButton({ text }: { text: string }) {
  const [state, setState] = useState<'idle' | 'copied' | 'blocked'>('idle')
  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text)
          setState('copied')
        } catch {
          setState('blocked')
        }
        window.setTimeout(() => setState('idle'), 1600)
      }}
      className="h-7 rounded border border-white/15 bg-white/5 px-2.5 font-mono text-[12px] text-[#ececea] hover:bg-white/10"
    >
      <span aria-live="polite">
        {state === 'copied' ? 'Copied' : state === 'blocked' ? 'Select to copy' : 'Copy'}
      </span>
    </button>
  )
}
