# Knowledge Pack Source Summary

## Extracted Sources

- `docs/参考资料/取水许可办理需资料及流程.docx`
- `docs/参考资料/填报说明.docx`
- `docs/参考资料/申请书.docx`
- `docs/参考资料/营业执照.jpg`
- `docs/参考资料/身份证.jpg`

The three docx files were unpacked and extracted into:

- `research/process-extracted.txt`
- `research/instructions-extracted.txt`
- `research/application-extracted.txt`

## MVP Material Scope

MVP fixed slots follow `.trellis/spec/backend/smartwater-mvp-contracts.md`:

- `APPLICATION_FORM`
- `BUSINESS_LICENSE`
- `ID_CARD`

The process document also lists application report, third-party interest statement, water resource assessment, permit application, engineering acceptance application, and engineering/facility acceptance report. Those are kept as future or review-hint materials, not MVP upload slots.

## Field Rule Basis

The field rules are sourced from `填报说明.docx` and aligned to the MVP domain contract fields:

- Applicant identity and credential fields: applicant name, unified social credit code or ID number, legal representative, registered address.
- Contact fields: business address, contact name, mobile phone.
- Project fields: project name, project nature, project overview, annual withdrawal total, application reason, requested start date and term.
- Water source fields: source type, administrative location, intake position, source amount, facility type, water use type, measurement method, return water information.

## Manual Review Only Rules

The following are explicitly marked manual review only:

- Whether a scenario does not require a water permit.
- Public notice need and third-party interest impact.
- Approval authority for cross-administrative-region scenarios.
- Water resource assessment category and expert review requirements.
- Multi-applicant and multi-water-source cases unsupported by MVP.
- Extension, change, or re-application cases.
- Low OCR confidence for critical fields.

These rules generate review hints and basis references. They must not produce final approval or rejection language.
