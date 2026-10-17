import type { Metadata } from 'next'
import Link from 'next/link'

import { CHAPTERS } from '@/lib/workshop'

export const metadata: Metadata = { title: 'Workshop' }

export default function WorkshopPage() {
  const minutes = CHAPTERS.reduce((sum, chapter) => sum + chapter.minutes, 0)
  return (
    <div className="mx-auto max-w-3xl px-4 pt-14 pb-24">
      <header className="mb-10 flex flex-col gap-3">
        <p className="font-mono text-[12px] tracking-wider text-muted uppercase">
          {CHAPTERS.length} chapters · {minutes} minutes
        </p>
        <h1 className="text-[2.5rem] leading-tight font-semibold tracking-[-0.03em]">
          The workshop
        </h1>
        <p className="text-[17px] leading-relaxed text-ink-2">
          From a single sign-on flow you can watch step by step to a database that keeps customers
          apart on its own. Work through them in order; each ends with a way to check it worked.
        </p>
      </header>
      <ol className="border-t border-line">
        {CHAPTERS.map((chapter) => (
          <li key={chapter.slug} className="border-b border-line">
            <Link
              href={`/workshop/${chapter.slug}`}
              className="flex items-start gap-4 py-5 hover:bg-surface"
            >
              <span className="w-7 shrink-0 pt-0.5 font-mono text-[13px] text-muted">
                {chapter.number}
              </span>
              <span className="flex min-w-0 flex-col gap-1">
                <span className="text-[17px] font-semibold">{chapter.title}</span>
                <span className="text-[15px] text-ink-2">{chapter.summary}</span>
              </span>
              <span className="ml-auto shrink-0 pt-1 font-mono text-[12px] text-muted">
                {chapter.minutes} min
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  )
}
