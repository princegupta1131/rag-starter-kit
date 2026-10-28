// Renders an answer's Markdown (lists, bold, tables) and turns [n] into clickable citation chips.

import type { MouseEvent } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  text: string
  sourceAnchor?: (n: number) => string // id of the source element a chip jumps to
}

export default function AnswerText({ text, sourceAnchor }: Props) {
  const withLinks = sourceAnchor
    ? text.replace(/\[(\d+)\](?!\()/g, (_, n: string) => `[${n}](#${sourceAnchor(Number(n))})`)
    : text
  return (
    <div className="answer">
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) =>
            href?.startsWith('#') ? (
              <a className="cite" href={href} onClick={(e) => jumpTo(e, href)}>{children}</a>
            ) : (
              <a href={href} target="_blank" rel="noreferrer">{children}</a>
            ),
        }}
      >
        {withLinks}
      </Markdown>
    </div>
  )
}

function jumpTo(e: MouseEvent, href: string) {
  e.preventDefault()
  const target = document.getElementById(href.slice(1))
  if (!target) return
  target.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  target.classList.add('flash')
  setTimeout(() => target.classList.remove('flash'), 1200)
}
