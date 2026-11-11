import type { ComponentProps } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import AuthImage from '@/components/ui/AuthImage'

// A chat reply as the assistant writes it: headings, lists, tables, code, links and images. react-markdown builds React
// elements (never raw HTML), so a reply cannot inject markup. Images of the app itself (violation snapshots, at
// /api/...) are behind the login, so they go through AuthImage, which fetches them with the Authorization header.
const components: ComponentProps<typeof ReactMarkdown>['components'] = {
  p: ({ children }) => <p className="my-1.5 first:mt-0 last:mb-0">{children}</p>,
  h1: ({ children }) => <h3 className="mb-1 mt-2.5 text-[13px] font-bold">{children}</h3>,
  h2: ({ children }) => <h3 className="mb-1 mt-2.5 text-[13px] font-bold">{children}</h3>,
  h3: ({ children }) => <h4 className="mb-1 mt-2 text-xs font-bold">{children}</h4>,
  h4: ({ children }) => <h4 className="mb-1 mt-2 text-xs font-semibold">{children}</h4>,
  ul: ({ children }) => <ul className="my-1.5 list-disc space-y-0.5 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="my-1.5 list-decimal space-y-0.5 pl-5">{children}</ol>,
  li: ({ children }) => <li className="pl-0.5">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noreferrer" className="text-cyan-400 underline underline-offset-2 hover:text-cyan-300">
      {children}
    </a>
  ),
  blockquote: ({ children }) => <blockquote className="my-1.5 border-l-2 border-line-strong pl-2.5 text-dim">{children}</blockquote>,
  hr: () => <hr className="my-2 border-line" />,
  code: ({ className, children }) =>
    className?.startsWith('language-') ? (
      <code className="font-mono text-[11px]">{children}</code>
    ) : (
      <code className="rounded bg-black/30 px-1 py-px font-mono text-[11px] text-cyan-200">{children}</code>
    ),
  pre: ({ children }) => (
    <pre className="my-1.5 overflow-x-auto rounded border border-line bg-black/40 p-2 text-[11px] leading-snug">{children}</pre>
  ),
  table: ({ children }) => (
    <div className="my-2 overflow-x-auto rounded border border-line">
      <table className="w-full border-collapse text-left text-[11px]">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-panel text-dim">{children}</thead>,
  th: ({ children }) => <th className="border-b border-line px-2 py-1 font-semibold">{children}</th>,
  td: ({ children }) => <td className="border-t border-line/60 px-2 py-1 align-top">{children}</td>,
  img: ({ src, alt }) =>
    typeof src === 'string' && src.startsWith('/api/') ? (
      <AuthImage src={src} alt={alt} className="my-1.5 max-h-48 rounded border border-line bg-black object-contain" />
    ) : (
      <span className="text-dim">[{alt || 'image'}]</span> // an outside image is not loaded: it would tell its owner who reads the chat
    ),
}

export default function Markdown({ source }: { source: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {source}
    </ReactMarkdown>
  )
}
