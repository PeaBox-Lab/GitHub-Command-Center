# Windows Validation

v3.52 adds a dedicated Windows validation workflow on `windows-latest`.

Checks include Python compilation, the complete automated test suite, Git availability, core package imports, Tkinter availability, and startup import profiling. CI uploads `windows-validation.json` and `startup-performance.json` as evidence.

The Linux build environment cannot substitute for this Windows CI evidence; executable/installer validation remains the responsibility of the Windows workflows introduced in v3.47.
