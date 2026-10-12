import { useMemo } from "react";
import { marked } from "marked";
import DOMPurify from "dompurify";

// Links open in a new tab without access to this page.
DOMPurify.addHook("afterSanitizeAttributes", (node) => {
  if (node.tagName === "A") {
    node.setAttribute("target", "_blank");
    node.setAttribute("rel", "noopener noreferrer nofollow");
  }
});

export function renderMarkdown(md) {
  const html = marked.parse(md ?? "", { breaks: true });
  // img is blocked so a generated document can't ping a third-party server.
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ["style", "img", "form", "input", "button", "textarea", "select"],
  });
}

export default function Markdown({ text }) {
  const html = useMemo(() => renderMarkdown(text), [text]);
  return <div className="md" dangerouslySetInnerHTML={{ __html: html }} />;
}