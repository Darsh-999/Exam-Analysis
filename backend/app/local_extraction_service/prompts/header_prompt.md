Extract the exam paper's header metadata from the images below, following the schema
and rules in your system instructions.

## Metadata Extraction

- `degree`: raw degree text exactly as seen on the paper header (exclude semester or
  other info). Not found → `""`.
- `subject_name`: raw subject name exactly as seen in the first-page header/title. Not
  found → `""`.
- `subject_code`: raw subject code exactly as seen in the first-page header/title. Not
  found → `""`.
- `exam_date`: convert to `YYYY/MM/DD`. Not found → `""`.
- `semester`: integer 1–24. Convert Roman numerals ("III" → 3) and text variants
  ("Third Semester" → 3) to a number. Not found → `0`.
- `total_marks`: from "Total Marks" / "Maximum Marks" / "Max. Marks". Not found → `0`.
