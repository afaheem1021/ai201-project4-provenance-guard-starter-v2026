# Attack verdicts (attack_run_2026-11-08_1401_after.md)

Produced by `tools/judge_attacks.py`. Rules are in that file's docstring.

| ID | Family | Status | Guess | Score | Model | Style | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | 200 | unsure | 0.3054 | 0.1635 | 0.6365 | BROKE |
| EV02 | evasion | 200 | unsure | 0.5074 | 0.5943 | 0.3048 | BROKE |
| EV03 | evasion | 200 | unsure | 0.6144 | 0.6662 | 0.4937 | BROKE |
| EV04 | evasion | 200 | unsure | 0.6162 | 0.6114 | 0.6274 | BROKE |
| EV05 | evasion | 200 | unsure | 0.3467 | 0.3212 | 0.4062 | BROKE |
| EV06 | evasion | 200 | unsure | 0.4771 | 0.5727 | 0.2542 | BROKE |
| EV07 | evasion | 200 | unsure | 0.5603 | 0.5862 | 0.5000 | BROKE |
| EV08 | evasion | 400 | — | — | — | — | HELD |
| EV09 | evasion | 200 | unsure | 0.6388 | 0.7042 | 0.4862 | BROKE |
| EV10 | evasion | 200 | ai | 0.9027 | 0.9792 | 0.7241 | HELD |
| FP01 | false_positive | 200 | unsure | 0.5947 | 0.6175 | 0.5415 | HELD |
| FP02 | false_positive | 200 | unsure | 0.7114 | 0.7387 | 0.6476 | HELD |
| FP03 | false_positive | 200 | unsure | 0.7446 | 0.8051 | 0.6033 | HELD |
| FP04 | false_positive | 200 | unsure | 0.7486 | 0.8329 | 0.5520 | HELD |
| FP05 | false_positive | 200 | unsure | 0.7577 | 0.8005 | 0.6579 | HELD |
| FP06 | false_positive | 200 | unsure | 0.7699 | 0.8814 | 0.5097 | HELD |
| FP07 | false_positive | 200 | unsure | 0.7610 | 0.8816 | 0.4796 | HELD |
| FP08 | false_positive | 400 | — | — | — | — | HELD |
| PI01 | prompt_injection | 200 | unsure | 0.4412 | 0.4625 | 0.3915 | HELD |
| PI02 | prompt_injection | 200 | unsure | 0.2554 | 0.2044 | 0.3744 | HELD |
| PI03 | prompt_injection | 200 | unsure | 0.5803 | 0.5943 | 0.5478 | HELD |
| PI04 | prompt_injection | 200 | unsure | 0.5007 | 0.4998 | 0.5027 | HELD |
| PI05 | prompt_injection | 200 | unsure | 0.5641 | 0.6401 | 0.3868 | HELD |
| PI06 | prompt_injection | 200 | unsure | 0.5548 | 0.5583 | 0.5467 | HELD |
| MF01 | malformed | 400 | — | — | — | — | HELD |
| MF02 | malformed | 400 | — | — | — | — | HELD |
| MF03 | malformed | 400 | — | — | — | — | HELD |
| MF04 | malformed | 400 | — | — | — | — | HELD |
| MF05 | malformed | 400 | — | — | — | — | HELD |
| MF06 | malformed | 400 | — | — | — | — | HELD |
| MF07 | malformed | 400 | — | — | — | — | HELD |
| MF08 | malformed | 413 | — | — | — | — | HELD |
| RQ01 | malformed | 400 | — | — | — | — | HELD |
| RQ02 | malformed | 400 | — | — | — | — | HELD |
| RQ03 | malformed | 400 | — | — | — | — | HELD |
| RQ04 | malformed | 400 | — | — | — | — | HELD |
| RQ05 | malformed | 400 | — | — | — | — | HELD |
| RQ06 | malformed | 400 | — | — | — | — | HELD |
| RQ07 | malformed | 400 | — | — | — | — | HELD |
| RQ08 | malformed | 400 | — | — | — | — | HELD |
| RQ09 | malformed | 400 | — | — | — | — | HELD |
| RQ10 | malformed | 400 | — | — | — | — | HELD |
| RQ11 | malformed | 400 | — | — | — | — | HELD |
| RQ12 | malformed | 400 | — | — | — | — | HELD |
| FL01_01 | flood_same_creator | 400 | — | — | — | — | HELD |
| FL01_02 | flood_same_creator | 400 | — | — | — | — | HELD |
| FL01_03 | flood_same_creator | 400 | — | — | — | — | HELD |
| FL01_04 | flood_same_creator | 400 | — | — | — | — | HELD |
| FL01_05 | flood_same_creator | 400 | — | — | — | — | HELD |
| FL01_06 | flood_same_creator | 400 | — | — | — | — | HELD |
| FL01_07 | flood_same_creator | 400 | — | — | — | — | HELD |
| FL01_08 | flood_same_creator | 400 | — | — | — | — | HELD |
| FL01_09 | flood_same_creator | 400 | — | — | — | — | HELD |
| FL01_10 | flood_same_creator | 400 | — | — | — | — | HELD |
| FL01_11 | flood_same_creator | 429 | — | — | — | — | HELD |
| FL01_12 | flood_same_creator | 429 | — | — | — | — | HELD |

| Family | Held | Broke |
|---|---|---|
| evasion | 2 | 8 |
| false_positive | 8 | 0 |
| flood_same_creator | 12 | 0 |
| malformed | 20 | 0 |
| prompt_injection | 6 | 0 |
| **total** | **48** | **8** |
