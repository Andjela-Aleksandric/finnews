import { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

// matematički zapis formule (kao na papiru)
export default function Tex({ tex, display = true, className = "" }) {
  const html = useMemo(() => katex.renderToString(tex, { displayMode: display, throwOnError: false, strict: false, output: "html" }), [tex, display]);
  return <span className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}
