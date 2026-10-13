<!-- coast-standards-release: 1.12.1 -->
# Rules for AI features

The project may edit these rules. The bracket says how a rule is checked. A filed decision is one recorded in the project.

## Scope (AIS)

- **AIS-1** An AI feature sends data to a generative model, runs one on device, or shows model output. [check: context]

## Disclosure and labelling (DISC)

- **DISC-1** Before the first exchange, say plainly that the person is talking to a model. [check: review]
- **DISC-2** Generated media shown or exported carries machine-readable content credentials in the file. [check: review]
- **DISC-3** Label summaries or rewrites of a person's own content as generated. [check: review]
- **DISC-4** No text claims the model diagnoses, predicts, triages or treats a condition unless the product is cleared to. [check: review]

## Consent and data flow (FLOW)

- **FLOW-1** Send personal data to a model provider only after in-app consent naming the provider and data, not just a privacy policy. [check: review]
- **FLOW-2** Never send health or clinical data to a third-party model for marketing, ads or data mining, even with consent. [check: review]
- **FLOW-3** Send only allow-listed needed fields, stripped of identifiers, contacts and unneeded free text. [check: review]
- **FLOW-4** Inferring emotion or intent from voice, face or body signals needs a filed decision naming the legal basis. Text is allowed. [check: review]

## Prompt construction and injection defence (PROMPT)

- **PROMPT-1** Build every prompt in one place from a named template in version control. [check: review]
- **PROMPT-2** Outside content (pages, files, messages, documents, tool results) enters prompts as data, never instructions; the template says so. [check: review]
- **PROMPT-3** No secrets, keys, internal URLs or other people's data in prompts. [check: scan:secret-literal, review]
- **PROMPT-4** Call models via the backend or a proxy; never ship a provider key. [check: review]

## Output handling (OUT)

- **OUT-1** Validate model output like user input before executing, rendering as markup, or passing it to a shell, database or URL opener. [check: review]
- **OUT-2** Output that triggers a payment, deletion or message needs on-screen confirmation first. [check: review]
- **OUT-3** The person can flag model output in place. [check: review]
- **OUT-4** Show the source with each factual claim, or say there is none. [check: review]

## Tools and agency (AGENT)

- **AGENT-1** Models call only declared tools, each with one job, typed input and no more authority than the person. [check: review]
- **AGENT-2** Tools that write, send, pay or delete need confirmation each time or a revocable standing permission. [check: review]
- **AGENT-3** Agent loops have a step limit and timeout that stop the loop and tell the person. [check: review]
- **AGENT-4** Pin MCP servers and tool hosts by version, review their tool lists, and treat results as untrusted. [check: review]

## Cost controls (COST)

- **COST-1** Every call sets a max output length and checks a per-person, per-day feature budget first. [check: review]
- **COST-2** Retries are limited and back off. [check: review]
- **COST-3** Spend is measured per feature and visible to the team, or the feature does not ship. [check: review]

## Reliability (REL)

- **REL-1** Every call has a timeout and a plain-language fallback for a slow, down or refusing model. [check: review]
- **REL-2** A model outage affects only its feature, never the app. [check: review]
- **REL-3** Provider, model name and version are configuration read in one place. [check: scan:env-literal, review]

## Evaluation and regression testing (EVAL)

- **EVAL-1** Each feature has example inputs with expected output properties, run in CI on the pinned model after any prompt, model or retrieval change. [check: review]
- **EVAL-2** Output tests check shape, bounds, required fields and forbidden content, or use a grader, never exact text. [check: review]
- **EVAL-3** Tests include fitting injection and jailbreak attempts; each must fail. [check: review]

## Logging and personal data (LOG)

- **LOG-1** Log prompts and outputs only with consent, for the stated purpose, with personal data masked. [check: review]
- **LOG-2** Each call logs request id, template and model versions and token counts, not prompt text. [check: review]
- **LOG-3** Model-traffic logs are deleted on a set retention schedule. [check: review]

## Retrieval (RAG)

- **RAG-1** Filter documents by the person's access rights before retrieval, never after. [check: review]
- **RAG-2** Retrieved text is untrusted data (PROMPT-2). [check: review]
- **RAG-3** Embeddings of personal data follow their source data's storage and deletion rules. [check: review]

## Supply chain (SUPPLY)

- **SUPPLY-1** Pin model files and AI libraries by version or hash, from a named source in the dependency record. [check: review]
- **SUPPLY-2** Check an outside model's or dataset's licence and provenance before use. [check: review]

## Store submission gate (STORE)

- **STORE-1** Before submission, describe AI features truthfully and complete the store AI declarations (Google Play's asset-level one; Apple 4.7, 5.1.2(i)). [check: process]
- **STORE-2** Chatbots and generated content ship with OUT-3 and an age rating covering possible output. [check: process]

## EU classification gate (EU)

- **EU-1** A feature ships only with a filed EU AI Act class (prohibited, high-risk, transparency-only, none) and article. [check: process]
- **EU-2** Apps on the market before 2 August 2026 add DISC-2 by 2 December 2026; new apps ship with it. [check: process]

## Sources

- OWASP AISVS v1.0: <https://github.com/OWASP/AISVS> (CC BY-SA 4.0)
- OWASP LLM Top 10 2026: <https://github.com/GenAI-Security-Project/GenAI-LLM-Top10> (CC BY-SA 4.0)
- OWASP Top 10 for Agentic Applications 2026: <https://genai.owasp.org> (CC BY-SA 4.0)
- OWASP AI Testing Guide: <https://owasp.org/www-project-ai-testing-guide/>
- NIST AI 600-1 (public domain)
- C2PA 2.4: <https://c2pa.org> (CC BY 4.0)
- EU AI Act 2024/1689 as amended by 2026/1744: EUR-Lex
- Apple App Review Guidelines; Google Play Developer Policy
