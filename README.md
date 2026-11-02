# GitHub Command Center v3.63.0

Version 3.63 continues debt reduction while making the nine primary navigation groups easier to understand.

## Debt reduction
- Retired duplicate Sync Center implementation in favor of the extracted async Push & Pull Center
- Retired duplicate Release Policy Center implementation in favor of Public Release Readiness
- Compatibility aliases preserve old internal names and functionality
- Architecture budgets lowered again

## Friendlier navigation
The same nine task groups remain, but each now has one obvious primary action, two secondary actions, a plain-language description and short help text. User-facing labels avoid internal version suffixes even when the destination class remains V2 internally.

## Usability regression protection
- Structural navigation policy tests
- Unique destination tests
- Help-text coverage tests
- Maximum three primary actions per navigation group
- Expanded Windows UI regression to instantiate Changes, History, Review, Release Evidence, Branch Dashboard and Recovery Dashboard at the existing resolution/scaling matrix
