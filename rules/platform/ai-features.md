<!-- coast-rules-version: 8 -->
# Rules for AI features

This file ships with your project as a curated default, installed when you
tell Coast your app has AI features. Like the project rules, **it belongs to
you.** Edit any rule, delete what doesn't apply, and add your own on top.
Automated reviewers check every code change against exactly the rules in
this file, so a rule you add here is enforced on every change from then on.

How to read a rule: each one has an id (used in reviews, tickets, and
tests), a single checkable statement, and the source it rests on in
brackets. The sources are cited by requirement id or chapter; no text from
them is reproduced (see Sources at the bottom). Keep new rules checkable — a
reviewer must be able to answer "does this change break the rule — yes or
no?"

## Scope (AIS)

- **AIS-1** A feature counts as an AI feature when the app sends anything to
  a generative model, runs one on the device, or shows a person content a
  model produced. The rules below apply to every such feature; the rest of
  the app keeps the project rules only. [Coast's own scope line; Google Play's
  AI-generated content policy draws a narrower scope for its OWN purposes — see
  STORE; check: context]

## Disclosure and labelling (DISC)

- **DISC-1** Where a person interacts with a model (chat, assistant, voice),
  the screen says so in plain words before the first exchange — never a
  hidden bot. [EU AI Act Art. 50(1); NIST AI 600-1; check: review]
- **DISC-2** Text, images, audio or video the app generates and shows or
  exports carry a machine-readable mark that they are generated. The mark
  travels with the file (content credentials), not only with the screen.
  [EU AI Act Art. 50(2) — live since 2 August 2026; C2PA 2.4; check: review]
- **DISC-3** A generated summary or rewrite of a person's OWN content is
  labelled generated on screen even when the export carve-out may apply;
  the app never relies on the carve-out silently. [EU AI Act Art. 50(2) — the
  carve-out's reach is unsettled; Coast default, veto-able; check: review]
- **DISC-4** No screen, listing or marketing copy claims the model can
  diagnose, predict, triage, or treat a medical condition unless the product
  is classified and cleared to make that claim. [Google Play health apps policy;
  EU AI Act Annex III (the claim is the trigger); check: review]

## Consent and data flow (FLOW)

- **FLOW-1** Before any personal data leaves the device for a model
  provider, the person gives affirmative in-app consent on a screen that
  names the provider and what is sent — a privacy-policy mention is not
  consent. [Google Play User Data policy, prominent disclosure; Apple App Review
  5.1.2(i); check: review]
- **FLOW-2** Health data from the platform's health store and clinical data
  are never sent to a third-party model for marketing, advertising, or
  use-based data mining — no consent screen unlocks this. [Apple App Review 5.1.3;
  Google Play Health Connect policy; check: review]
- **FLOW-3** The data sent to a model is the minimum the feature needs:
  fields are allow-listed, and identifiers, contacts, and free-text not
  needed for the answer are stripped before the request. [AISVS v1.0 C2 Input
  Validation; LLM02:2026; check: review]
- **FLOW-4** Inferring a person's emotion or intention from biometric data
  (voice, face, physiological signals) is not built without a filed
  decision naming the legal basis — it is a high-risk use. Inference from
  typed or transcribed text is not biometric and is allowed under these
  rules. [EU AI Act Annex III; Art. 50(3); check: review]

## Prompt construction and injection defence (PROMPT)

- **PROMPT-1** Every prompt is assembled in one place from a named template
  in version control; no screen or view model builds prompt strings
  inline. [AISVS v1.0 C3 Model Lifecycle Management & Change Control; Coast DRY
  rule; check: review]
- **PROMPT-2** Content from outside the app — web pages, files, messages,
  retrieved documents, tool results — is placed in the prompt as data, never
  as instructions, and the template says so to the model. [LLM01:2026 Prompt
  Injection; AISVS v1.0 C2; check: review]
- **PROMPT-3** Secrets, keys, internal URLs and other people's data never
  appear in a prompt or a system instruction. [LLM08:2026 Hidden Context Exposure;
  LLM02:2026; check: scan:secret-literal, review]
- **PROMPT-4** Model calls go through the app's own backend or a provider
  proxy; a provider API key is never shipped inside the app. [AISVS v1.0 C5 Access
  Control & Identity; OWASP MASVS; check: review]

## Output handling (OUT)

- **OUT-1** Model output is treated as untrusted input: it is never
  executed, evaluated, rendered as HTML/markup, or passed to a shell,
  database or URL opener without the same validation any user input gets.
  [LLM10:2026 Improper Output Handling; AISVS v1.0 C7 Model Behavior, Output
  Control & Safety Assurance; check: review]
- **OUT-2** Output that drives a decision with consequences (a payment, a
  deletion, a message to someone else) is confirmed by the person on screen
  before it takes effect. [LLM03:2026 Excessive Agency; check: review]
- **OUT-3** Every place a person sees model output offers a way to report or
  flag it, inside the app, without leaving the screen. [Google Play AI- generated
  content policy — the one hard requirement; check: review]
- **OUT-4** Factual claims the model makes are shown with their source when
  the feature has one (retrieval, a document), and the screen says when it
  has none. [LLM07:2026 Misinformation; check: review]

## Tools and agency (AGENT)

- **AGENT-1** A model may call only the tools the feature declares; each
  tool has one job, a typed input, and no more authority than the person
  using the app has. [LLM03:2026; AISVS v1.0 C9 Orchestration & Agentic Security;
  OWASP Top 10 for Agentic Applications 2026; check: review]
- **AGENT-2** Tools that change state (write, send, pay, delete) require the
  person's confirmation each time, or an explicit standing permission the
  person granted on screen and can revoke. [LLM03:2026; check: review]
- **AGENT-3** An agent loop has a fixed maximum number of steps and a
  timeout; hitting either stops the loop and tells the person. [AISVS v1.0 C9;
  LLM06:2026 Unbounded Consumption; check: review]
- **AGENT-4** Model Context Protocol servers and other tool hosts are
  pinned, their tool lists reviewed at connect time, and their results
  treated as untrusted input. [AISVS v1.0 C10 Model Context Protocol (MCP)
  Security; check: review]

## Cost controls (COST)

- **COST-1** Every model call carries a maximum output length, and every
  feature has a per-person and per-day budget the app enforces before
  calling. [LLM06:2026 Unbounded Consumption; check: review]
- **COST-2** Retries on provider errors are bounded and backed off; a loop
  that retries a model call is a defect. [LLM06:2026; check: review]
- **COST-3** Spend per feature is metered and visible to the team; a feature
  that cannot report what it costs does not ship. [Coast default, veto-able;
  check: review]

## Reliability (REL)

- **REL-1** Every model call has a timeout and a plain-words fallback the
  person sees when the model is slow, down, or refuses; the feature never
  spins without end. [AISVS v1.0 C12 Monitoring, Logging & Anomaly Detection;
  check: review]
- **REL-2** The app works without the AI feature: a model outage degrades
  one feature, never the whole app. [Coast default, veto-able; check: review]
- **REL-3** Provider, model name and version are configuration read in one
  place, so a model change is one diff and one review. [AISVS v1.0 C3; check:
  scan:env-literal, review]

## Evaluation and regression testing (EVAL)

- **EVAL-1** Each AI feature ships with a written set of example inputs and
  expected properties of the output (not exact text), run in CI against the
  pinned model; a change to the prompt, the model, or the retrieval runs
  them. [AISVS v1.0 C3; OWASP AI Testing Guide; check: review]
- **EVAL-2** Tests of model output assert deterministic properties (shape,
  bounds, required fields, forbidden content) or use a separate grader;
  they never assert exact generated prose. [Coast default, veto-able — no primary
  source gives a rule for non-determinism; check: review]
- **EVAL-3** Known prompt-injection and jailbreak probes for the feature's
  shape are part of the suite and must fail to take control. [LLM01:2026; AISVS
  v1.0 C11 Adversarial Robustness; check: review]

## Logging and personal data (LOG)

- **LOG-1** Prompts and outputs are logged only when the person has agreed,
  only for the stated purpose, and with personal data removed or masked
  before they are stored. [AISVS v1.0 C12; LLM02:2026; check: review]
- **LOG-2** Every model call is traceable: a request id, the template
  version, the model version, and the token counts are recorded without the
  prompt text. [AISVS v1.0 C12; check: review]
- **LOG-3** Logs of model traffic have a retention period and are deleted
  on schedule. [AISVS v1.0 C12; check: review]

## Retrieval (RAG)

- **RAG-1** Documents a feature retrieves for the model are filtered by the
  person's own access rights before retrieval, never after. [LLM09:2026 Vector and
  Embedding Weaknesses; AISVS v1.0 C8 Memory, Embeddings & Vector Database
  Security; check: review]
- **RAG-2** Retrieved text is untrusted input (see PROMPT-2); a document
  can never instruct the model. [LLM01:2026; LLM09:2026; check: review]
- **RAG-3** Embeddings of personal data are stored and deleted under the
  same rules as the data they came from. [AISVS v1.0 C8; check: review]

## Supply chain (SUPPLY)

- **SUPPLY-1** Model weights, model files and AI libraries are pinned by
  version or hash, come from a named source, and are listed in the project's
  dependency record. [LLM04:2026 Supply Chain; AISVS v1.0 C6 Supply Chain Security
  for Models; check: review]
- **SUPPLY-2** A model or dataset from outside is checked for its licence
  and its provenance before it is used; "found on a hub" is not a source.
  [LLM04:2026; LLM05:2026 Data and Model Poisoning; check: review]

## Store submission gate (STORE)

- **STORE-1** Before submission, the app's AI features are described
  truthfully in the listing and the store's AI declarations are completed
  (Google Play's asset-level AI declaration is mandatory; Apple has no
  generative-AI guideline — only 4.7 for chatbots and 5.1.2(i) for sharing
  data with third-party AI apply). [Google Play Console requirements; Apple App
  Review 4.7, 5.1.2(i); check: process]
- **STORE-2** A chatbot or generated-content feature ships with the report
  control of OUT-3 and an age rating that accounts for what the model can
  produce. [Google Play AI-generated content policy; Apple App Review 4.7; check:
  process]

## EU classification gate (EU)

- **EU-1** Before an AI feature ships, a filed decision records its EU AI
  Act classification (prohibited, high-risk, transparency-only, or none)
  and the article it rests on; a feature with no filed classification does
  not ship. [EU AI Act as amended by Regulation (EU) 2026/1744 — Art. 50
  transparency duties apply since 2 August 2026; high-risk obligations follow
  from December 2027 / August 2028; check: process]
- **EU-2** An app placed on the market before 2 August 2026 completes its
  marking duty (DISC-2) by 2 December 2026; a new app ships with it from
  day one. [Regulation (EU) 2026/1744; check: process]

## Sources

- OWASP AI Security Verification Standard (AISVS) v1.0, chapters C1–C12 —
  <https://github.com/OWASP/AISVS> (CC BY-SA 4.0; cited by chapter, no text
  reproduced)
- OWASP GenAI LLM Top 10, 2026 edition (LLM01:2026 – LLM10:2026) —
  <https://github.com/GenAI-Security-Project/GenAI-LLM-Top10> (CC BY-SA 4.0;
  cited by entry id)
- OWASP Top 10 for Agentic Applications 2026 — <https://genai.owasp.org>
  (CC BY-SA 4.0; cited as a corpus)
- OWASP AI Testing Guide — <https://owasp.org/www-project-ai-testing-guide/>
- NIST AI 600-1, Generative AI Profile (public domain)
- C2PA 2.4 specification — <https://c2pa.org> (CC BY 4.0)
- EU AI Act, Regulation (EU) 2024/1689 as amended by Regulation (EU)
  2026/1744 — EUR-Lex
- Apple App Store Review Guidelines 4.7 and 5.1.2(i), 5.1.3; Google Play
  Developer Policy (AI-generated content, User Data, Health)

No text from these sources is reproduced here — every rule is an original
plain-language statement citing its source — so editing or replacing this
file carries no licence obligations for you.
