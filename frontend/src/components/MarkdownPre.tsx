import { isValidElement, type ReactNode } from 'react'

import { CopyButton } from './CopyButton'

// Code blocks in the chapters get a copy button. The text is pulled out of the rendered children.

function textOf(node: ReactNode): string {
  if (typeof node === 'string' || typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(textOf).join('')
  if (isValidElement<{ children?: ReactNode }>(node)) return textOf(node.props.children)
  return ''
}

export function MarkdownPre({ children }: { children?: ReactNode }) {
  const code = textOf(children).replace(/\n$/, '')
  return (
    <div className="code-block">
      <pre>{children}</pre>
      <CopyButton text={code} />
    </div>
  )
}
