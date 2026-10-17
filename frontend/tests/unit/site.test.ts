import fs from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { CHAPTERS, findChapter } from '@/lib/workshop'

const ROOT = path.join(process.cwd(), '..')

describe('chapters', () => {
  it('has seven chapters numbered in order', () => {
    expect(CHAPTERS.map((chapter) => chapter.number)).toEqual([
      '01',
      '02',
      '03',
      '04',
      '05',
      '06',
      '07',
    ])
  })

  it.each(CHAPTERS.map((chapter) => [chapter.slug, chapter] as const))(
    '%s has a summary, a time and the standard sections',
    (_slug, chapter) => {
      expect(chapter.summary.length).toBeGreaterThan(10)
      expect(chapter.minutes).toBeGreaterThan(0)
      expect(chapter.body).toMatch(/^## Goal$/m)
      expect(chapter.body).toMatch(/^## Check it works$/m)
      expect(chapter.body).toMatch(/^## Exercise$/m)
    },
  )

  it('only mentions files that exist', () => {
    const mentioned = new Set(
      CHAPTERS.flatMap((chapter) =>
        [...chapter.body.matchAll(/`((?:lab|\.github)\/[\w./-]+\.\w+)`/g)].map((m) => m[1] ?? ''),
      ),
    )
    expect(mentioned.size).toBeGreaterThan(4)
    for (const file of mentioned) {
      expect(fs.existsSync(path.join(ROOT, file)), `${file} is missing`).toBe(true)
    }
  })

  it.each([
    ['02-oauth-code-flow', 'lab/sso/idp.py', 'def pkce_challenge'],
    ['05-roles', 'lab/sso/rbac.py', 'PERMISSIONS:'],
    ['07-row-level-security', 'lab/postgres/rls.sql', 'ALTER TABLE invoices ENABLE'],
  ])('%s quotes %s exactly as it is', (slug, file, marker) => {
    const code = fs.readFileSync(path.join(ROOT, file), 'utf8')
    const start = code.indexOf(marker)
    const snippet = code.slice(start, code.indexOf('\n\n', start)).trimEnd()

    expect(start).toBeGreaterThanOrEqual(0)
    expect(findChapter(slug)?.body).toContain(snippet)
  })
})
