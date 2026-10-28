Rewrite the user's latest question into one standalone search query for a document search engine.

- Fix spelling mistakes.
- If it is a follow-up ("what about its side effects?"), replace pronouns with what they refer to, using the conversation.
- Expand abbreviations only when the conversation makes their meaning clear.
- Keep the user's meaning. Do not add topics, assumptions or details they did not ask about
  ("my order is late, what can I do?" -> "options when an order is delivered late", not "courier company contact details").
- Keep the original language. Do not answer the question.

Conversation so far:
{{history}}

Latest question: {{question}}

Return only the rewritten query, nothing else.
