import type { Metadata, Viewport } from 'next'
import { IBM_Plex_Mono, Plus_Jakarta_Sans } from 'next/font/google'

import { Shell } from '@/components/Shell'

import './globals.css'

const sans = Plus_Jakarta_Sans({
  variable: '--font-face-sans',
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
})
const mono = IBM_Plex_Mono({
  variable: '--font-face-mono',
  subsets: ['latin'],
  weight: ['400', '500'],
})

export const metadata: Metadata = {
  title: { default: 'Enterprise auth, hands on', template: '%s · Enterprise auth, hands on' },
  description:
    'A hands-on workshop on enterprise auth: run an OIDC single sign-on flow with PKCE, verify ID tokens, read SAML, map roles to permissions, find a cross-tenant leak and stop it with Postgres row-level security.',
}

export const viewport: Viewport = { themeColor: '#ffffff' }

export default function RootLayout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <a
          href="#main"
          className="sr-only bg-ink px-4 py-2 text-canvas focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50"
        >
          Skip to content
        </a>
        <Shell>{children}</Shell>
      </body>
    </html>
  )
}
