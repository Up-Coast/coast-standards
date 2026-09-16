<!-- coast-standards-release: 1.6.0 -->
# Rules for AI features

This file is a starting set of rules, installed when you tell Coast your app has AI features. Like the project rules, **it belongs to you.** Edit any rule, delete rules that don't apply, and add your own.

Automated reviewers check every code change against the rules in this file. A rule you add here applies to every change from then on.

How to read a rule:

- The id (for example `OUT-1`) is used in reviews, tickets and tests.
- The sentence after it is one checkable requirement.
- The brackets name the source and how the rule is checked. Sources are cited by requirement id or chapter; no text from them is copied (see Sources at the bottom).

Keep new rules checkable. A reviewer must be able to answer "does this change break the rule: yes or no?"

Some rules below need a "filed decision": a decision written down and kept on record in the project.

## Scope (AIS)

- **AIS-1** A feature is an AI feature if the app sends anything to a generative model, runs one on the device, or shows a person content a model produced. The rules below apply to every AI feature. The rest of the app follows only the project rules. [Coast's own scope line; Google Play's AI-generated content policy draws a narrower scope for its OWN purposes — see STORE; check: context]

## Disclosure and labelling (DISC)

- **DISC-1** When a person interacts with a model (chat, assistant, voice), the screen says so in plain words before the first exchange. Never hide that it is a bot. [EU AI Act Art. 50(1); NIST AI 600-1; check: review]
- **DISC-2** Generated text, images, audio or video that the app shows or exports carry a machine-readable mark saying they are generated. The mark travels with the file (content credentials), not only on the screen. [EU AI Act Art. 50(2) — live since 2 August 2026; C2PA 2.4; check: review]
- **DISC-3** A generated summary or rewrite of a person's OWN content is labelled as generated on screen, even when the law's exception for such content might apply. The app never quietly relies on that exception. [EU AI Act Art. 50(2) — the carve-out's reach is unsettled; Coast default, veto-able; check: review]
- **DISC-4** No screen, store listing or marketing text claims the model can diagnose, predict, triage or treat a medical condition, unless the product is classified and cleared to make that claim. [Google Play health apps policy; EU AI Act Annex III (the claim is the trigger); check: review]

## Consent and data flow (FLOW)

- **FLOW-1** Before any personal data leaves the device for a model provider, the person gives clear in-app consent. The consent screen names the provider and what is sent. A mention in the privacy policy is not consent. [Google Play User Data policy, prominent disclosure; Apple App Review 5.1.2(i); check: review]
- **FLOW-2** Never send health data from the platform's health store, or clinical data, to a third-party model for marketing, advertising or usage-based data mining. No consent screen makes this allowed. [Apple App Review 5.1.3; Google Play Health Connect policy; check: review]
- **FLOW-3** Send a model only the data the feature needs. Use an allow-list of fields. Before the request, strip identifiers, contacts and any free text the answer doesn't need. [AISVS v1.0 C2 Input Validation; LLM02:2026; check: review]
- **FLOW-4** Don't build a feature that infers a person's emotion or intention from biometric data (voice, face, physiological signals) without a filed decision naming the legal basis. It is a high-risk use. Inference from typed or transcribed text is not biometric and is allowed under these rules. [EU AI Act Annex III; Art. 50(3); check: review]

## Prompt construction and injection defence (PROMPT)

- **PROMPT-1** Build every prompt in one place, from a named template kept in version control. No screen or view model builds prompt strings inline. [AISVS v1.0 C3 Model Lifecycle Management & Change Control; Coast DRY rule; check: review]
- **PROMPT-2** Content from outside the app (web pages, files, messages, retrieved documents, tool results) goes into the prompt as data, never as instructions. The template tells the model this. [LLM01:2026 Prompt Injection; AISVS v1.0 C2; check: review]
- **PROMPT-3** Secrets, keys, internal URLs and other people's data never appear in a prompt or system instruction. [LLM08:2026 Hidden Context Exposure; LLM02:2026; check: scan:secret-literal, review]
- **PROMPT-4** Send model calls through the app's own backend or a provider proxy. Never ship a provider API key inside the app. [AISVS v1.0 C5 Access Control & Identity; OWASP MASVS; check: review]

## Output handling (OUT)

- **OUT-1** Treat model output as untrusted input. Never execute it, evaluate it, render it as HTML or markup, or pass it to a shell, database or URL opener without the same validation any user input gets. [LLM10:2026 Improper Output Handling; AISVS v1.0 C7 Model Behavior, Output Control & Safety Assurance; check: review]
- **OUT-2** If output drives an action with consequences (a payment, a deletion, a message to someone else), the person confirms it on screen before it takes effect. [LLM03:2026 Excessive Agency; check: review]
- **OUT-3** Wherever a person sees model output, they can report or flag it inside the app, without leaving the screen. [Google Play AI-generated content policy — the one hard requirement; check: review]
- **OUT-4** When the feature has a source for the model's factual claims (retrieval, a document), show the source with the claim. When it has none, the screen says so. [LLM07:2026 Misinformation; check: review]

## Tools and agency (AGENT)

- **AGENT-1** A model can call only the tools the feature declares. Each tool has one job, a typed input, and no more authority than the person using the app. [LLM03:2026; AISVS v1.0 C9 Orchestration & Agentic Security; OWASP Top 10 for Agentic Applications 2026; check: review]
- **AGENT-2** Tools that change state (write, send, pay, delete) need the person's confirmation every time, or a standing permission the person granted on screen and can revoke. [LLM03:2026; check: review]
- **AGENT-3** An agent loop has a fixed maximum number of steps and a timeout. Reaching either one stops the loop and tells the person. [AISVS v1.0 C9; LLM06:2026 Unbounded Consumption; check: review]
- **AGENT-4** Pin Model Context Protocol (MCP) servers and other tool hosts to a version. Review their tool lists when connecting. Treat their results as untrusted input. [AISVS v1.0 C10 Model Context Protocol (MCP) Security; check: review]

## Cost controls (COST)

- **COST-1** Every model call sets a maximum output length. Every feature has a per-person and per-day budget, and the app checks it before calling. [LLM06:2026 Unbounded Consumption; check: review]
- **COST-2** Retries after provider errors are limited in number and back off. A loop that keeps retrying a model call is a defect. [LLM06:2026; check: review]
- **COST-3** Measure spend per feature and make it visible to the team. A feature that can't report what it costs doesn't ship. [Coast default, veto-able; check: review]

## Reliability (REL)

- **REL-1** Every model call has a timeout. When the model is slow, down or refuses, the person sees a plain-language fallback. The feature never shows a spinner forever. [AISVS v1.0 C12 Monitoring, Logging & Anomaly Detection; check: review]
- **REL-2** The app works without the AI feature. A model outage affects that one feature, never the whole app. [Coast default, veto-able; check: review]
- **REL-3** Provider, model name and model version are configuration, read in one place. Changing the model takes one diff and one review. [AISVS v1.0 C3; check: scan:env-literal, review]

## Evaluation and regression testing (EVAL)

- **EVAL-1** Each AI feature ships with a written set of example inputs and the expected properties of the output (not exact text). They run in CI against the pinned model. Any change to the prompt, the model or the retrieval runs them. [AISVS v1.0 C3; OWASP AI Testing Guide; check: review]
- **EVAL-2** Tests of model output check deterministic properties (shape, bounds, required fields, forbidden content) or use a separate grader. They never check for exact generated text. [Coast default, veto-able — no primary source gives a rule for non-determinism; check: review]
- **EVAL-3** The test suite includes known prompt-injection and jailbreak attempts that fit the feature. Each must fail to take control. [LLM01:2026; AISVS v1.0 C11 Adversarial Robustness; check: review]

## Logging and personal data (LOG)

- **LOG-1** Log prompts and outputs only when the person has agreed, only for the stated purpose, and only after removing or masking personal data. [AISVS v1.0 C12; LLM02:2026; check: review]
- **LOG-2** Every model call can be traced. Record a request id, the template version, the model version and the token counts, without the prompt text. [AISVS v1.0 C12; check: review]
- **LOG-3** Logs of model traffic have a retention period and are deleted on schedule. [AISVS v1.0 C12; check: review]

## Retrieval (RAG)

- **RAG-1** Filter the documents a feature retrieves for the model by the person's own access rights before retrieval, never after. [LLM09:2026 Vector and Embedding Weaknesses; AISVS v1.0 C8 Memory, Embeddings & Vector Database Security; check: review]
- **RAG-2** Retrieved text is untrusted input (see PROMPT-2). A document can never give the model instructions. [LLM01:2026; LLM09:2026; check: review]
- **RAG-3** Store and delete embeddings of personal data under the same rules as the data they came from. [AISVS v1.0 C8; check: review]

## Supply chain (SUPPLY)

- **SUPPLY-1** Pin model weights, model files and AI libraries by version or hash. Each comes from a named source and is listed in the project's dependency record. [LLM04:2026 Supply Chain; AISVS v1.0 C6 Supply Chain Security for Models; check: review]
- **SUPPLY-2** Before using an outside model or dataset, check its licence and where it came from. "Found on a hub" is not a source. [LLM04:2026; LLM05:2026 Data and Model Poisoning; check: review]

## Store submission gate (STORE)

- **STORE-1** Before submitting to a store, describe the app's AI features truthfully in the listing and complete the store's AI declarations. Google Play's asset-level AI declaration is mandatory. Apple has no generative-AI guideline; only 4.7 (chatbots) and 5.1.2(i) (sharing data with third-party AI) apply. [Google Play Console requirements; Apple App Review 4.7, 5.1.2(i); check: process]
- **STORE-2** A chatbot or generated-content feature ships with the report control from OUT-3, and with an age rating that accounts for what the model can produce. [Google Play AI-generated content policy; Apple App Review 4.7; check: process]

## EU classification gate (EU)

- **EU-1** Before an AI feature ships, a filed decision records its EU AI Act classification (prohibited, high-risk, transparency-only, or none) and the article it is based on. A feature without a filed classification doesn't ship. [EU AI Act as amended by Regulation (EU) 2026/1744 — Art. 50 transparency duties apply since 2 August 2026; high-risk obligations follow from December 2027 / August 2028; check: process]
- **EU-2** An app on the market before 2 August 2026 must add the generated-content marking (DISC-2) by 2 December 2026. A new app ships with it from day one. [Regulation (EU) 2026/1744; check: process]

## Sources

- OWASP AI Security Verification Standard (AISVS) v1.0, chapters C1–C12 — <https://github.com/OWASP/AISVS> (CC BY-SA 4.0; cited by chapter, no text reproduced)
- OWASP GenAI LLM Top 10, 2026 edition (LLM01:2026 – LLM10:2026) — <https://github.com/GenAI-Security-Project/GenAI-LLM-Top10> (CC BY-SA 4.0; cited by entry id)
- OWASP Top 10 for Agentic Applications 2026 — <https://genai.owasp.org> (CC BY-SA 4.0; cited as a corpus)
- OWASP AI Testing Guide — <https://owasp.org/www-project-ai-testing-guide/>
- NIST AI 600-1, Generative AI Profile (public domain)
- C2PA 2.4 specification — <https://c2pa.org> (CC BY 4.0)
- EU AI Act, Regulation (EU) 2024/1689 as amended by Regulation (EU) 2026/1744 — EUR-Lex
- Apple App Store Review Guidelines 4.7 and 5.1.2(i), 5.1.3; Google Play Developer Policy (AI-generated content, User Data, Health)

No text from these sources is copied here. Every rule is written in our own words and cites its source, so you can edit or replace this file with no licence obligations.
