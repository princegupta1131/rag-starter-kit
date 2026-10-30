# Trainer notes: explaining RAG with the two labs

Use these notes with the two interactive pages in [`docs/explainers/`](explainers/):
**RAG Ingestion Lab** (how a document is prepared) and **RAG Retrieval Lab** (how a question is answered).
Every number below is real: it was measured on the sample handbook with the kit.

---

## 1. Start with the story (1 minute)

Say this before showing anything:

> "An AI model like Gemini knows a lot about the world, but it has **never seen our company documents**.
> If you ask it 'How many days of leave do I get?', it will **guess**.
> RAG fixes that in two phases.
> **First (ingestion)**, we prepare our documents so they can be searched by meaning.
> **Then (retrieval)**, for every question we find the right pieces of our documents, and the AI answers **only from those pieces**, with sources."

Draw this on the board:

```
INGESTION (once per document)
document → extract text → cut into chunks → turn each chunk into numbers (embedding) → save in Postgres

RETRIEVAL (every question)
question → turn into numbers → find the closest chunks → AI answers from them → check citations
```

---

## 2. The five ideas everything rests on

If trainees understand these five, they understand RAG. Use the analogies.

| Idea | Say it like this | Analogy |
|---|---|---|
| **RAG** | "Find the right pages first, then answer only from them." | An **open-book exam**: the student may only use the book, and must say which page. |
| **Chunk** | "We cut documents into small pieces of about 200 words, so we can find the exact piece that answers the question." | **Index cards**: you don't hand someone the whole book, you hand them the one card. |
| **Embedding** | "An AI model turns a piece of text into a list of 768 numbers. Texts with similar meaning get similar numbers." | **GPS coordinates for meaning**: places close on a map are close in real life; texts close in this "meaning space" mean similar things. |
| **Cosine similarity** | "We compare two lists of numbers by the angle between them. Same direction = same meaning." | Two **arrows**: pointing the same way = 1.0, at right angles = 0, opposite = −1. |
| **Vector index (HNSW)** | "With millions of chunks we can't compare with every one. The index jumps between neighbours to get close fast." | A **road map**: highways first to reach the right city, then local roads to the street. |

The one sentence to repeat all session:
> **"Keyword search matches letters. Meaning search matches ideas."**

---

## 3. Ingestion: what to say and click

Open **RAG Ingestion Lab** (part 1). It follows one example the whole way: the handbook, and Priya asking
*"Can I carry over unused holidays?"*. The page is a set of **missions**. Each one opens with a question
(read it out and let the room guess), then trainees play. The answer card stays locked until they've tried it,
and the bar at the top counts their discoveries. Under each mission: **Why** · **The science** · **In the kit**, and a closed **Go deeper**.

Colours mean the same thing on both pages: **blue** = document, **amber** = question, **green** = exact words, **red** = stopped.

### Mission 1 · X-ray the file (Extraction) · 2 min
- **Ask:** "A file is full of hidden junk the AI can't use. What's really inside one?"
- **Click** *Scan the file* (or drag the scanner down). The Word file's XML burns away and only the handbook's words stay.
- **Try** *PDF file* and *Markdown file*: different junk, same plain words at the end.
- **Say:** "The search and the AI only need words. We keep the page number so answers can say *page 3*. Pictures are described in words by a vision model."
- **Point:** garbage in, garbage out. Bad extraction (scanned PDFs, scrambled Hindi PDFs) means bad answers.

### Mission 2 · Slice the handbook into cards (Chunking) · 5 min
- **Ask:** "Too small and a card loses its context. Too big and it's about everything. Where's the sweet spot?"
- **Click** *Small · 60 words* → *✂ Slice!*: many focused cards. Then *Big · 400 words*: one card about everything. Watch the focus and context gauges.
- **Click** *Kit · 200 words*: the balance. Bonus: ask a trainee to tap the card that holds "carried over".
- **Point at the amber text** on the page: "That's the overlap: each card repeats the end of the previous one (40 words), so nothing is lost at the border."

### Mission 3 · Turn meaning into a place in space (Embedding) · 8 min, the key step
- **Ask:** "Priya says *holidays*. The handbook says *unused days*. How can a computer know they mean the same?"
- **Click** *Feed the model*: the card's words go in and **768 real numbers** light up. Hover one: "No single number means anything. Together they're a place."
- **The Meaning Galaxy:** let trainees pick a question card, **guess** where it will land, then *Launch the question*.
  - *Can I carry over unused holidays?* → lands next to the carry-over rule, **0.80**, with almost no shared words.
  - The **Hindi** question → lands next to the English leave rule, **0.72**.
  - *Stock price?* → no real home: the closest card is only 0.55.
- **Turn on** the *Keyword flashlight*: only cards with the exact same words light up. For Hindi, nothing does, yet meaning still finds the rule.
- **Say:** "The model was trained on billions of examples: same meaning pulled together, different meaning pushed apart."

### Mission 4 · The arrow duel (Cosine similarity) · 5 min
- **Ask:** "Each list of 768 numbers is an arrow. Can you guess the angle between two meanings?"
- **Play the 4 rounds.** Trainees drag the amber arrow and *Lock in my guess*. The real arrow then swings to the true angle and points are given:
  - holiday ↔ vacation **0.88** · carry-over rule **0.80** · sick leave **0.64** · password + 2FA **0.53**
- **The surprise (round 4):** a sentence about passwords has nothing to do with holidays, yet scores 0.53, not 0. "With this model, *unrelated* sits around 0.5. That's why the kit **ranks** cards and has a bar of **0.50**."
- **Point:** change the arrow's length and the score doesn't move. "Cosine ignores length, so a short question can match a long paragraph."
- **Go deeper:** the formula `cosine = (A·B) / (|A| × |B|)` with a worked example.

### Mission 5 · Save it, then race to find it (Postgres + pgvector) · 5 min
- **Click** *Save to Postgres*: the 2 real cards fly into the database and their rows appear (words, 768 numbers, keywords).
- **Say:** "One row per card, all in Postgres. Meaning search, word search and normal SQL on the same data."
- **Ask:** "With 10 million cards, how does it find the closest one in milliseconds?" Then *Start the race*: *check every card* vs *use the index*. Click a lane to move the question; try *3,000 cards* and the gap grows.
- **Say:** "The HNSW index is like highways on a map: it hops towards the answer instead of checking every card." (The race is a simulation; the label on the page says so.)

**Wrap up:** read the **What we have now** box. "This happens **once**, at upload. Now, what happens when Priya asks?"

---

## 4. Retrieval: what to say and click

Open **RAG Retrieval Lab** (part 2). At the top, trainees **pick one question** and follow it through all 9 checkpoints:
*Can I carry over unused holidays?*, *How many days of annual leave do I get?*, the Hindi question, or *Stock price?*.
Changing the question resets every checkpoint. Start with Priya's question, then repeat with Hindi and stock price for the twists.

### 1 · Get past the door (Guard) · 2 min
- **Ask:** "Can you get a trick past the guard?" Use the presets, or let a trainee type.
- **Click** *Knock on the door*. Priya's question passes (3 lamps go green). The trick, the 1,200-character essay and the empty question bounce back with the kit's real messages.
- **Say:** "Plain rules, no AI, under a millisecond. A bad input stopped here costs nothing."

### 2 · Ask it twice (Cache) · 1 min
- **Click** *Ask*: the question runs the whole pipe (about 4 s, example times). *Ask* again: instant, from memory.
- **Click** *Upload a new document*, then *Ask*: the document fingerprint changes, so it runs in full again.
- **Say:** "Same question in the last 10 minutes and the same documents → answered from memory."

### 3 · Finish the thought (Rewrite) · 1 min
- **Click** *Search "until when?" as it is*: the words *until* and *when* are thrown away, nothing left to search.
- **Click** *Let the AI complete it* → *until when can unused annual leave be carried over*. "A quick AI call. Only the search uses it."

### 4 · Launch it into meaning space (Embedding) · 2 min
- **Click** *Launch the question*: it lands in the same galaxy as Lab 1, next to the carry-over rule (**0.80**).
- **Say:** "Same model as the handbook = same map. Numbers from different models can't be compared."

### 5 · The race: meaning vs exact words (Hybrid search) · 4 min
- **Click** *Start the race*. Meaning (a librarian who understands) vs exact words (like Ctrl+F, on the roots `carri`, `unus`, `holiday`).
- **Say:** "Both agree here: the carry-over rule is first."
- **Switch to Hindi:** exact words **trips**, it finds nothing; meaning still finds the leave rule. "That's why we use both."

### 6 · The podium (Rank fusion) · 3 min
- **Ask:** "One judge scores 0.80, the other 0.3. You can't add those. How do you pick a winner?"
- **Click** *Award the points*: points by position from each list, stacked; the carry-over rule takes gold.
- **Say:** "Two judges ranking dancers: each gives points by position, add them up. We keep the best 6."
- **Go deeper:** the formula `1 / (60 + position)` for every card.

### 7 · Clear the bar (Evidence gate) · 4 min
- **Click** *Jump!*: the best match jumps over the 0.50 bar. Drag the bar above it and jump again → knocked down, **no AI call**. *Back to the kit's 0.50*.
- **Switch to stock price:** it **clears** the bar at 0.55 (a sentence about a learning *budget* is loosely similar).
- **Say the key sentence:** **"Similar is not the same as answered."**

### 8 · The open-book exam (Grounded generation) · 3 min
- **Ask:** "The AI knows a lot about the world. Why don't we let it use what it knows?"
- **Click** *Write the answer*: the 4 rules and the numbered sources it gets, then the answer with its source glowing.
- **Say:** "Only these pages, cite every fact, answer in the question's language, and say NOT_FOUND if the answer isn't there."
- **Stock question:** the AI writes **NOT_FOUND**: safety net 2 (net 1 was the gate).
- **Leave question:** the real kit answer, "24 days of paid annual leave per calendar year [1]".

### 9 · Spot the fake citation (Citation check) · 2 min
- **Ask:** "Can you spot the invented source before Priya sees it?" Let trainees tap the citation they think is fake.
- **Click** *Run the kit's check*: the fake number disappears, the rest are renumbered from [1], and the final reply shows only the cited source.
- **Say:** "No AI here: code makes sure every [number] points to a real source."

**Wrap up:** click *Replay the journey* for the chosen question (a stop at the gate shows in red). "Every question: about 4 seconds, mostly the two AI calls."

---

## 5. Session plan (about 75 minutes)

| Time | What | Where |
|---|---|---|
| 0–5 | The story + the board diagram | Section 1 of these notes |
| 5–10 | The five ideas with analogies | Section 2 |
| 10–40 | Ingestion lab, mission by mission | RAG Ingestion Lab |
| 40–65 | Retrieval lab, checkpoint by checkpoint | RAG Retrieval Lab |
| 65–75 | Live in the app: upload the handbook, ask the 5 questions, open "How this answer was made" | The kit (`make run`) |

Then the hands-on exercises: [docs/HANDS_ON.md](HANDS_ON.md).

---

## 6. Questions trainees ask (and short answers)

**Why not just give the whole document to the AI?**
Small documents: you can. Real collections are thousands of pages: too long for the model, slow and expensive, and the AI gets distracted. RAG sends only the few relevant chunks.

**Why not fine-tune the model on our documents instead?**
Fine-tuning teaches style, not reliable facts. It's slow and costly to update, and can't cite a source. RAG updates instantly when you upload a file, and every answer shows where it came from.

**What exactly are the 768 numbers?**
Positions on 768 learned "directions" of meaning. No single number has a human meaning; together they place the text in meaning space.

**Why 768?**
It's the size this model (gemini-embedding-001) is configured for in the kit. More numbers can capture more detail but cost more storage and time. It's fixed once the table is created.

**Can I mix embeddings from two models?**
No. Each model has its own meaning space; their numbers aren't comparable. That's why the kit stores the model name per document and marks old ones "upload again".

**Why cosine and not normal distance?**
Cosine compares direction only, so text length doesn't change the score. For text embeddings this works best.

**What is a "good" similarity score?**
Depends on the model. With this one: real matches about 0.65–0.80, unrelated text about 0.45–0.55. That's why the gate is 0.50. Always tune it on your own questions.

**Why also keyword search? Isn't meaning search enough?**
Meaning search can blur exact terms: product codes, names, acronyms like 2FA. Keyword search catches those. Together they cover both.

**How does it work across languages?**
The embedding model was trained on many languages, so "छुट्टी" and "leave" land close in meaning space. Keyword search can't do that (0 matches for the Hindi question).

**Can RAG still be wrong?**
Yes, if the right chunk isn't found, or the document itself is wrong. That's why there are two safety nets (the gate and NOT_FOUND) and why every answer shows its sources for the user to check.

**What is HNSW, in one line?**
An index that links each vector to its nearest neighbours in layers, so a search hops towards the answer instead of checking every row.

**Why Postgres and not a "vector database"?**
pgvector makes Postgres one. You keep one database for text, vectors, keywords and normal data, with backups, permissions and SQL you already know.

**What does chunk overlap cost?**
A little extra storage (repeated words). It's worth it so ideas at a border aren't lost.

**Where would I change things in the kit?**
`backend/.env`: CHUNK_SIZE_WORDS, MIN_SIMILARITY, TOP_K. The answer rules: `backend/app/retrieval_service/prompts/answer_system.md`.

---

## 7. Cheat sheet: numbers to remember

| Setting / fact | Value |
|---|---|
| Chunk size / overlap | 200 words / 40 words |
| Embedding model / size | gemini-embedding-001 / 768 numbers |
| Similarity | cosine, 1.0 = same direction |
| Candidates per search | 20 (meaning) + 20 (keyword) |
| Fusion | 1 / (60 + rank), keep top 6 |
| Evidence gate | MIN_SIMILARITY 0.50 |
| Context margin | within 0.12 of the best |
| Cache | 10 minutes, reset when documents change |
| "holidays" vs carry-over rule | 0.796, 2 words in common |
| Hindi question vs leave rule | 0.722, 0 words in common |
| Stock-price question | passes gate at 0.55, AI says NOT_FOUND |
| HNSW demo | 140 comparisons (exact) vs 19 (HNSW) |
