# Upload Gradle test reports on failure

A failed Gradle test task prints only the exception type and the test name in the job log. It doesn't print the message or the stack trace, and the HTML and XML reports aren't uploaded. For example, smokinglog-android run 42569618661 failed with `NoClassDefFoundError` and no class name.

## Steps

1. In `.github/actions/gradle-build/action.yml`, after the Gradle step, add an `actions/upload-artifact@v7` step with `if: failure()`:
   - `name: test-reports`;
   - path `${{ inputs.working-directory }}/**/build/reports/tests/` and `${{ inputs.working-directory }}/**/build/test-results/`;
   - `if-no-files-found: ignore`;
   - a short `retention-days`, such as 7.
2. Verify that a failing test in a consumer PR produces a `test-reports` artifact whose `index.html` shows the stack trace.
3. Note the artifact in the README section for the Android workflows.
