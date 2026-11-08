# Attack run — after

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-08 14:01
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `b2fc96d1-84c1-4061-9829-28acccb951ea` | unsure | 0.305 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `5ab661ba-d1bb-48da-8af9-ba60bf73f3c6` | unsure | 0.507 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `7b06649b-b7e9-4a6b-aeeb-3601343f3983` | unsure | 0.614 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `869d9d20-ac11-4049-a570-caeb87f57574` | unsure | 0.616 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `ac5a3152-62c0-45bf-8953-3fce1ccb77d6` | unsure | 0.347 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `4d194e1e-c6a5-46d8-a260-6bc9c0dd4489` | unsure | 0.477 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `c2f3a3f5-deb7-45d9-b6b5-220df46b4f96` | unsure | 0.560 |  |
| EV08 | evasion | signal one: text below the token window | 400 | `—` | — | — |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `3b446b0c-19c9-4b98-9941-4bc6e09a09bd` | unsure | 0.639 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `984abd72-e908-461d-a610-3ac1aa1481d0` | ai | 0.903 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `d3dce608-880f-49a3-b661-178df1736358` | unsure | 0.595 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `01a75f60-c74e-45b7-b199-57225044d415` | unsure | 0.711 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `14b9338b-6374-4d62-8565-6f694d98e8b4` | unsure | 0.745 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `6eea0151-5b9f-47d5-b075-2459e4905a87` | unsure | 0.749 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `49738888-507c-469d-b631-6026e4d88002` | unsure | 0.758 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `b5ec74ef-7f4b-40e5-8d58-87157d5933b3` | unsure | 0.770 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `abbf4328-e6b3-4dad-96e8-6cde9c8484ec` | unsure | 0.761 |  |
| FP08 | false_positive | very short genuine human submission | 400 | `—` | — | — |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `94d8c4e2-7e0c-47b5-832d-fd2521575162` | unsure | 0.441 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `5059d92a-7e06-467f-b440-92288c135d16` | unsure | 0.255 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `a59aece7-4ef1-4fe8-b7de-71771cab9d0a` | unsure | 0.580 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `a5230b3f-dd22-41fa-a6fe-0486c603e87c` | unsure | 0.501 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `48ed4718-940c-4f73-bbad-04f46c4b0ce5` | unsure | 0.564 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `e6981ba9-6eca-4bcb-b124-209e6dedc74a` | unsure | 0.555 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 400 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 400 | `—` | — | — |  |
| MF04 | malformed | text is only punctuation | 400 | `—` | — | — |  |
| MF05 | malformed | text is a very long single word | 400 | `—` | — | — |  |
| MF06 | malformed | text is emoji only | 400 | `—` | — | — |  |
| MF07 | malformed | text is right-to-left script | 400 | `—` | — | — |  |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — |  |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — |  |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — |  |
| RQ03 | malformed | text is a number | 400 | `—` | — | — |  |
| RQ04 | malformed | text is a list | 400 | `—` | — | — |  |
| RQ05 | malformed | text is null | 400 | `—` | — | — |  |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — |  |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — |  |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — |  |
| RQ09 | malformed | body is empty | 400 | `—` | — | — |  |
| RQ10 | malformed | body is form-encoded, not JSON | 400 | `—` | — | — |  |
| RQ11 | malformed | body is JSON claiming to be plain text | 400 | `—` | — | — |  |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — |  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "b2fc96d1-84c1-4061-9829-28acccb951ea",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "confidence": 0.3054,
  "model_score": 0.1635,
  "style_score": 0.6365,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "5ab661ba-d1bb-48da-8af9-ba60bf73f3c6",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.5074,
  "model_score": 0.5943,
  "style_score": 0.3048,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "7b06649b-b7e9-4a6b-aeeb-3601343f3983",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.6144,
  "model_score": 0.6662,
  "style_score": 0.4937,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "869d9d20-ac11-4049-a570-caeb87f57574",
  "creator_id": "attacker_EV04",
  "guess": "unsure",
  "confidence": 0.6162,
  "model_score": 0.6114,
  "style_score": 0.6274,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "ac5a3152-62c0-45bf-8953-3fce1ccb77d6",
  "creator_id": "attacker_EV05",
  "guess": "unsure",
  "confidence": 0.3467,
  "model_score": 0.3212,
  "style_score": 0.4062,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "4d194e1e-c6a5-46d8-a260-6bc9c0dd4489",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.4771,
  "model_score": 0.5727,
  "style_score": 0.2542,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "c2f3a3f5-deb7-45d9-b6b5-220df46b4f96",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.5603,
  "model_score": 0.5862,
  "style_score": 0.5,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_EV08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "3b446b0c-19c9-4b98-9941-4bc6e09a09bd",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.6388,
  "model_score": 0.7042,
  "style_score": 0.4862,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "984abd72-e908-461d-a610-3ac1aa1481d0",
  "creator_id": "attacker_EV10",
  "guess": "ai",
  "confidence": 0.9027,
  "model_score": 0.9792,
  "style_score": 0.7241,
  "label": "We think this may have been generated by AI. This estimate can be wrong and is not proof. If you wrote it, you can appeal and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "d3dce608-880f-49a3-b661-178df1736358",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.5947,
  "model_score": 0.6175,
  "style_score": 0.5415,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "01a75f60-c74e-45b7-b199-57225044d415",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.7114,
  "model_score": 0.7387,
  "style_score": 0.6476,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "14b9338b-6374-4d62-8565-6f694d98e8b4",
  "creator_id": "attacker_FP03",
  "guess": "unsure",
  "confidence": 0.7446,
  "model_score": 0.8051,
  "style_score": 0.6033,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "6eea0151-5b9f-47d5-b075-2459e4905a87",
  "creator_id": "attacker_FP04",
  "guess": "unsure",
  "confidence": 0.7486,
  "model_score": 0.8329,
  "style_score": 0.552,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "49738888-507c-469d-b631-6026e4d88002",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "confidence": 0.7577,
  "model_score": 0.8005,
  "style_score": 0.6579,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "b5ec74ef-7f4b-40e5-8d58-87157d5933b3",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.7699,
  "model_score": 0.8814,
  "style_score": 0.5097,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "abbf4328-e6b3-4dad-96e8-6cde9c8484ec",
  "creator_id": "attacker_FP07",
  "guess": "unsure",
  "confidence": 0.761,
  "model_score": 0.8816,
  "style_score": 0.4796,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_FP08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "94d8c4e2-7e0c-47b5-832d-fd2521575162",
  "creator_id": "attacker_PI01",
  "guess": "unsure",
  "confidence": 0.4412,
  "model_score": 0.4625,
  "style_score": 0.3915,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "5059d92a-7e06-467f-b440-92288c135d16",
  "creator_id": "attacker_PI02",
  "guess": "unsure",
  "confidence": 0.2554,
  "model_score": 0.2044,
  "style_score": 0.3744,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "a59aece7-4ef1-4fe8-b7de-71771cab9d0a",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.5803,
  "model_score": 0.5943,
  "style_score": 0.5478,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "a5230b3f-dd22-41fa-a6fe-0486c603e87c",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.5007,
  "model_score": 0.4998,
  "style_score": 0.5027,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "48ed4718-940c-4f73-bbad-04f46c4b0ce5",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.5641,
  "model_score": 0.6401,
  "style_score": 0.3868,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "e6981ba9-6eca-4bcb-b124-209e6dedc74a",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.5548,
  "model_score": 0.5583,
  "style_score": 0.5467,
  "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF06",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF07",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
