/**
 * Minimal Python syntax highlighter — deliberately not a dependency
 * (react-syntax-highlighter/prismjs would roughly double the already-large
 * main bundle, see the code-splitting note in App.tsx). Tokenizes just
 * enough to make model-generated Python readable at a glance: keywords,
 * strings, comments, numbers, function/class names. Not a general-purpose
 * lexer — doesn't need to be, since every input here is LLM-generated
 * Python, not arbitrary source.
 *
 * Belongs to: frontend/src/lib/
 * Phase: hardening pass (post-audit) — audit flagged CodeViewer as plain
 * <pre> text with no highlighting.
 */
import type { ReactNode } from "react";

const KEYWORDS = new Set([
  "def", "return", "if", "elif", "else", "for", "while", "in", "not", "and", "or",
  "import", "from", "as", "class", "try", "except", "finally", "raise", "with",
  "pass", "break", "continue", "lambda", "yield", "None", "True", "False",
  "is", "assert", "global", "nonlocal", "async", "await", "del",
]);

const TOKEN_RE = /(#.*$)|('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")|(\b\d+\.?\d*\b)|(\b[A-Za-z_][A-Za-z0-9_]*\b)|([^\s])/gm;

export function highlightPython(code: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let match: RegExpExecArray | null;
  let key = 0;
  let lastIndex = 0;

  while ((match = TOKEN_RE.exec(code)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(code.slice(lastIndex, match.index));
    }
    const [full, comment, string, number, word] = match;
    if (comment) {
      nodes.push(<span key={key++} className="text-mist italic">{comment}</span>);
    } else if (string) {
      nodes.push(<span key={key++} className="text-channel-3">{string}</span>);
    } else if (number) {
      nodes.push(<span key={key++} className="text-channel-5">{number}</span>);
    } else if (word && KEYWORDS.has(word)) {
      nodes.push(<span key={key++} className="text-channel-2 font-medium">{word}</span>);
    } else {
      nodes.push(full);
    }
    lastIndex = match.index + full.length;
  }
  if (lastIndex < code.length) {
    nodes.push(code.slice(lastIndex));
  }
  return nodes;
}
