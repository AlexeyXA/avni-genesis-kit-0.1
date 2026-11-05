# Security Policy

## Supported versions

This is an experimental MVP. Security fixes, if any, will be published for the latest tagged release only.

## What this project is not

AVNI Genesis Kit is **not** a security sandbox. Acceptance tests run agent code in a subprocess with a timeout and a reduced environment. The process retains the privileges of the current user and may still reach the network.

Do not use this tool to execute untrusted packages.

## Reporting a vulnerability

If you believe you have found a vulnerability in packaging, path handling, secret scanning, or signature verification, please open a private security advisory or contact the maintainers through the repository.

Do not include secrets or production credentials in public issues.
