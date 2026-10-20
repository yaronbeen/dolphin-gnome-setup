# Security and public repository boundary

This repository is public. It contains generic executable helpers, menu templates,
tests, and setup documentation, not a backup of a user's home or configuration.

Never commit:
- SSH private keys, API keys, passwords, tokens, or environment files.
- Contabo private configuration or upload history/download URLs.
- rclone configuration, Google Drive credentials, or private folder mappings.
- Browser profiles, desktop screenshots, or unrelated desktop settings.

The upload client loads configuration at runtime from the user's home directory.
It uses strict SSH host-key checking and a configured SSH key. It does not embed
server credentials. The repository does not configure or deploy the remote server.

Menu commands pass filenames as separate arguments, not interpolated shell code.
Conversions encode in a private temporary directory beside the source, then
publish via a hard link that fails if the destination already exists. This needs
a filesystem that supports hard links. Output permissions cannot exceed the
source file's read/write permissions. Executable bits are not copied. An
unsupported filesystem produces an error rather than a less-safe fallback.

Media is decoded by locally installed Pillow, ffmpeg, exiftool and mediainfo.
Keep those system packages patched; these helpers do not sandbox media parsers.
Conversions can use significant CPU, disk and memory on large files.

Before publishing, scan both the worktree and Git history, with credential
verification disabled so suspected secrets are not sent to providers:

```bash
trufflehog filesystem --no-update --no-verification --fail .
trufflehog git --no-update --no-verification --fail file://"$PWD"
```

No scanner can prove the absence of secrets. Review the exact staged file list
and diff as well; `.gitignore` is only a guardrail. Never publish scanner output
containing a detected secret.
