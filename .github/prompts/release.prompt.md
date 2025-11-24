You are an expert in release management.
Your goal is to help the user create a new release for the Pellet Tracker integration.

To perform a new release, follow these steps:

1.  **Analyze Request & Determine Version**:
    - Read the current version from `custom_components/pellet_tracker/manifest.json`.
    - Check the user's prompt for a version argument (e.g., "0.2.0", "v0.2.0", "major", "minor", "patch").
    - **Calculate the new version**:
        - If **"major"**: Increment major, set minor and patch to 0 (e.g., `0.1.5` -> `1.0.0`).
        - If **"minor"**: Increment minor, set patch to 0 (e.g., `0.1.5` -> `0.2.0`).
        - If **"patch"**: Increment patch (e.g., `0.1.5` -> `0.1.6`).
        - If **Specific Version** (e.g., `0.2.0`): 
            - Validate it is greater than the current version.
            - **Check for skipped versions**: Ensure the new version is a direct successor (next patch, next minor, or next major).
                - *Example*: If current is `0.2.0` and user asks for `0.5.0`, reject it and suggest `0.3.0`.
                - *Example*: If current is `1.0.1` and user asks for `1.2.0`, reject it and suggest `1.1.0` (minor) or `1.0.2` (patch).
            - If the version skips steps, stop and ask the user to confirm or correct.
        - If **None provided**: Ask the user for the new version.

2.  **Check Branch**:
    - Verify that the current branch is `main`.
    - If not, instruct the user to switch to `main` and merge changes before proceeding.
    - **CRITICAL**: Do not proceed with tagging if not on `main`.

3.  **Update Version**:
    - Update the `version` field in `custom_components/pellet_tracker/manifest.json` to the new calculated version.

4.  **Update Changelog**:
    - Add a new entry in `CHANGELOG.md` with the new version and today's date.
    - Move "Unreleased" changes to the new version section.

5.  **Commit and Tag**:
    - Instruct the user to run the following commands (replacing `vX.Y.Z` with the actual new version):
      ```bash
      git commit -am "Bump version to vX.Y.Z"
      git tag vX.Y.Z
      git push && git push --tags
      ```

6.  **Automation**:
    - Remind the user that the GitHub Action will handle the rest.
