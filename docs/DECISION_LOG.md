# Decision log

## 2026-08-31 — Signal synchronization and window eligibility

- Accepted the BIDS event mapping at speech-envelope resolution after both
  pilot runs passed a preregistered median-correlation/residual timing gate.
- Did not interpret the monitor and WAV signals as sample-identical; analog
  monitor filtering and channel differences remain visible.
- Froze audit profile `audit_v1`: complete non-overlapping five-second windows
  anchored at EEG run time zero, with corresponding audio required in bounds.
- Froze Silero VAD 6.2.1 defaults at 16 kHz on vocal WAV channel 0 and retained
  windows with at least 20% detected speech.
- These are reproducible audit choices because the anchor paper leaves window
  origin, Silero version, channel selection, and VAD parameters unresolved.

## 2026-08-30 — Project rename

- Renamed the project from JapanEEG Speech-Decoding Audit to Non-Invasive
  Speech Decoding.
- The broader name reflects that JapanEEG is the primary dataset rather than
  the permanent boundary of the research program.
- Reproduction and construct-validity analyses remain central methods, without
  defining the project solely as an audit.

## 2026-08-29 — Repository initialization

- Chosen project name: JapanEEG Speech-Decoding Audit.
- Primary focus: distinguish neural scaling from myogenic, acoustic, session,
  device, and lexical explanations.
- Primary confirmation unit: held-out recording session or day.
- Random-window splitting is retained only for paper-matched reproduction.
- Raw data and generated outputs are excluded from version control.
- All experiment configurations remain `draft` until the data and methods audit
  is complete.
