## Tests (TEST)

- **TEST-1** Every acceptance criterion has an automated test that names it. [check: scan:test-criterion-tag]
- **TEST-2** Merge-gating tests fake every outside service; live tests never block a merge. [check: scan:hermetic-test]
- **TEST-3** A test fails when its behaviour breaks; assertions any code passes are not coverage. [check: review]
- **TEST-4** Fixtures match real data's size and mess (overflowing lists, truncating names), and fakes return real failures (403, 404, empty, unreachable, slow). [check: review]
- **TEST-5** Every screen showing project data has a stress test past its limits: huge, empty and boundary inputs, slow and missing responses. [check: review]
- **TEST-6** Test each result an outside call can return (answer, refusal, timeout, empty, wrong shape), checking what the person sees and can do next. [check: review]
- **TEST-7** A flow is done only when its builder has used it in the built product (window, settings, navigation, relaunch), saving screen captures and reading stored data back after each action. [check: process, review]
