# Writing Jira Rich Text Through the Atlassian MCP — Shared Resource

Read this before any Jira rich-text write. `SHARED-AGENT-GUIDANCE.md` § Writing rich text through
the Atlassian MCP points every client here, and `groom-card-for-verification` follows it for its description write. It is a supporting
resource, not a skill: it is never discoverable or invocable on its own.

Applies to any rich-text field — `editJiraIssue` / `createJiraIssue` descriptions and
`addCommentToJiraIssue` bodies.

**Format: send `contentFormat: "markdown"`.** The live `contentFormat` enum is the authority for
what is accepted, and each value carries its own usage hint, so read the schema of the call you are
about to make rather than trusting a rule here. Do not consult `getContentFormatGuide` for a Jira
write: it covers the Confluence page tools only, and its own description names the two it serves.

Markdown produces real structure, not literal markup: verified 2026-09-15 on ENG-546, whose
markdown description renders as genuine `<h2>` headings, an ordered list, monospace spans and an
auto-linked issue macro, and 2026-09-30 on ENG-526, whose fenced code blocks render as code panels
(detail under the braces trap below).

**Escaping traps.** None is visible in the schema, which is why they live here. The markdown is
converted to Jira wiki markup before it renders, so a code span becomes wiki monospace and any wiki
inline marker inside it, or touching its edge, can still be read as markup. Verified on ENG-546
(2026-09-15) and ENG-578 (2026-09-22):

- A code span **inside** a bold run ends the bold early, so the rest of the sentence renders
  unbolded. Keep code spans outside the bold, or drop one of the two.
- Braces **inside** a code span corrupt it, and can take the surrounding block structure with
  them. A `{` or `}` within it reads as wiki macro syntax: on ENG-546 a `{id}` path placeholder
  broke its own span, cost the next list item its numbering and leaked a literal `#` into the
  text. Write the placeholder without braces. For anything longer than a name, a fenced block is
  the safer home: on ENG-526 (2026-09-30) six fenced blocks tagged `sql`, each at paragraph
  level, rendered as Jira code panels with SQL highlighting, and their parentheses, quoted
  strings, commas, semicolons and `@` variables all came through intact. Still untested inside a
  fence: braces, square brackets, backslashes, plus signs, angle brackets (that SQL used `BETWEEN`
  rather than `>=`, so none appeared), and a fence nested inside a list item.
- Square brackets and backslashes **inside** a code span break it: `[` … `]` reads as a wiki link
  and renders as an error span, and `\` reads as a forced line break. On ENG-578 a regex such as
  `0[0-3]\d` came out as a broken link, a line break and a stray `d`. Describe character classes
  in words, or keep regexes out of Jira.
- A code span that is **only a plus sign**, or ends with one, closes a wiki `+inserted+` run. It
  pairs with an earlier plus-leading span in the same paragraph (a phone number such as `+4420…`)
  and everything between renders as underlined inserted text; on ENG-578 three paragraphs went
  that way. Write "plus sign" or "plus-prefixed" in prose. A plus followed by digits inside a
  span is fine on its own.
- A hyphen **touching** a code span's edge (`` `+`-prefixed … single-`0` ``) pairs with the next
  hyphen touching a span as wiki strikethrough. Put a space between the span and the hyphen, or
  reword.

**Verification needs the rendered view.** Read the field back with `expand: "renderedFields"` and
check the HTML. A plain read-back proves nothing: the description returns as markdown whichever
`responseContentFormat` you ask for, `adf` included, so literal `##` and a real heading look
identical. The ENG-546 corruption above stayed invisible until the rendered view was read.

When editing existing rich content, preserve everything outside the edit you were authorised to
make.
