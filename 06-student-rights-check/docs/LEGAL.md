# Legal approach

## The problem

German law restricts legal services. The Rechtsdienstleistungsgesetz (RDG) prohibits legal services without authorisation, meaning a legal assessment of a specific individual case. General legal information is allowed because it is not advice on an individual case. Legal commentators largely agree that a disclaimer saying "this is not legal advice" changes nothing if the tool actually gives case-specific advice.

So "AI lawyer" is the wrong product. Student Rights Check is a **legal information and red-flag tool** that sends people to those who are allowed to advise them.

## Design rules

1. **Only verified statements.** Every legal statement lives in `knowledge_base/laws.json` with the paragraph, a source link and a verification date. The LLM cannot add new legal claims.
2. **General, not individual.** Wording is always "the law generally says...", with exceptions mentioned where they are common.
3. **Uncertainty is visible.** "Red flag" only where a clause clearly conflicts with a rule. Everything that depends on details is "get it checked". Questions without a confident match get no answer.
4. **Always a human next step.** Every report and answer lists free advice services for that area.
5. **No storage.** Documents and questions are processed in memory. Nothing is logged or used for training.
6. **Regional scope is explicit.** Exam law is verified for Bavaria (RaPO, BayHIG, AGVwGO). Rent-brake and rent-increase values are marked as Munich/Bavaria.

## Keeping the knowledge base current

Values that change are stored with their validity year (minimum wage 2026/2027, Minijob limit 2026/2027). The engine picks the value valid on the day of the check. Planned but not yet enacted changes (e.g. the BAföG reform) are described as plans, not as law. `_meta.last_verified` is shown in every output. Before each release, every entry is checked again.

## Sources checked on 2026-11-08

**Exams (Bavaria)**
- § 9 Abs. 3 RaPO – exam withdrawal (as quoted in BayVGH decisions and university guidance, e.g. TH Aschaffenburg)
- Art. 12 AGVwGO – optional objection procedure for personal exam decisions: https://www.gesetze-bayern.de/Content/Pdf/BayAGVwGO-12?all=False
- Nachteilsausgleich under BayHIG: University of Regensburg guidance
- § 1 Abs. 2 Nr. 8, § 3 MuSchG – maternity protection for students

**Work**
- MiLoV5 (minimum wage 13.90 € / 14.60 €), § 22 MiLoG (internships)
- Werkstudentenprivileg – Deutsche Rentenversicherung
- Minijob limit 603 € (2026) / 633 € (2027) – Deutsche Rentenversicherung press release 22.12.2025
- § 3 EFZG, § 3 BUrlG, § 622, § 623 BGB, § 108, § 109 GewO

**International students**
- § 16b Abs. 3 AufenthG – 140 full / 280 half days (since 1 March 2024)

**Housing**
- § 548, § 551, § 553, § 556d, § 558, § 573c, § 536, § 536c BGB
- Bavarian Mieterschutzverordnung from 1 January 2026 (285 municipalities, until 31.12.2029) – Bavarian Ministry of Justice press release
- BGH VIII ZR 228/23 (28.01.2026) – no subletting for profit
- §§ 17, 19 BMG – registration

**Added in v0.3**
- BGH VIII ZR 185/14, VIII ZR 361/03 – cosmetic repairs; § 556 Abs. 3, § 573, § 575 BGB
- §§ 3–5 ArbZG; § 8 Abs. 1 Nr. 2 SGB IV (short-term jobs, DRV press release June 2026); § 4 TzBfG and BAG 5 AZR 108/22
- Interview questions: BAG 2 AZR 621/01 ('right to lie')
- § 20 Abs. 2 WoGG (Studierendenwerke); § 31 ZKG; § 56 TKG; §§ 312j, 312k, 241a BGB

**Money, health, contracts, data, discrimination**
- §§ 13, 13a BAföG (992 € maximum); reform draft of 12 August 2026
- §§ 32, 66 EStG (Kindergeld 259 €), § 32a EStG (Grundfreibetrag 12,348 € in 2026)
- § 4 RBStV – broadcasting fee exemption
- § 5 Abs. 1 Nr. 9, § 10 SGB V – student and family health insurance
- §§ 309 Nr. 9, 355, 356 BGB
- Art. 12, 15 DSGVO
- §§ 19, 21 AGG; BGH I ZR 129/25 (29.01.2026) – estate agents liable

**RDG and AI**
- beck-aktuell, "Darf ChatGPT Jura?" (Nov 2025)
