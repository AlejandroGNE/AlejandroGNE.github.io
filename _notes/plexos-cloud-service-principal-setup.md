---
title: "PLEXOS from Mac: Set Up Service-Principal Credentials"
date: 2026-10-24
description: "Obtain PLEXOS Cloud service-principal credentials and save a private local file for CLI authentication from a Mac-hosted Linux container."
---

The PLEXOS Cloud CLI automates workflows such as submitting simulations and downloading results. It is distributed for Windows and Linux, with no native Mac package in the Marketplace I checked. To use it from my Mac, I run the Linux CLI inside a Docker container.

Browser-based SSO did not work from that container in my setup. Service-principal authentication lets the CLI log in automatically without opening a browser.

This note covers obtaining service-principal credentials and saving them on your Mac, ready for use by the CLI inside a Linux container.

## Before you begin

Confirm that no one else is using service-principal credentials in your tenant before generating or regenerating keys.

## 1. Open Access Keys

Sign into PLEXOS Cloud using your usual browser login.

To reach the credentials page:

1. Open the left navigation menu and select **Admin**. If you cannot see **Admin**, ask your administrator to complete this process and share the credentials with you.
2. Open **User Settings**, then select **Add New User** to reach Central License Manager.
3. In Central License Manager, open the left navigation menu and select **Access Keys**.

You do not need to submit a new user form; continue to **Access Keys**.

## 2. Get your credentials

If this is the first setup, select **GENERATE KEYS**. If the page already shows regeneration controls, select **REGENERATE PRIMARY SECRET**.

The **Access Key Details** dialog provides:

| Field | Used for |
|---|---|
| Tenant ID | `PXC_TENANT_ID` |
| Client ID | `PXC_CLIENT_ID` |
| Primary Secret | `PXC_CLIENT_SECRET` |

Keep the dialog open while completing the next step. **COPY CONTENT** copies the details together; the terminal prompts below take each value separately.

## 3. Save the credentials on your Mac

Open **Terminal** on your Mac. Copy and paste the entire block below, then press **Enter**. Paste each requested value and press **Enter** after each one. Your input will be hidden.

```bash
/bin/bash <<'PLEXOS_SETUP'
set +x
set -e
umask 077

folder="$HOME/.config/plexos-cloud"
file="$folder/service-principal.env"
mkdir -p "$folder"
chmod 700 "$folder"

if [[ -e "$file" ]]; then
  printf 'A credentials file already exists at %s. It was not changed.\n' "$file"
  exit 1
fi

for name in PXC_TENANT_ID PXC_CLIENT_ID PXC_CLIENT_SECRET; do
  IFS= read -r -s -p "$name: " value </dev/tty
  printf '\n' >/dev/tty
  if [[ -z "$value" ]]; then
    printf 'No value entered. Run the setup again.\n'
    exit 1
  fi
  printf -v "$name" '%s' "$value"
done

set -C
exec 3>"$file"
for name in PXC_TENANT_ID PXC_CLIENT_ID PXC_CLIENT_SECRET; do
  printf '%s=%q\n' "$name" "${!name}" >&3
done
exec 3>&-
printf 'Credentials saved to %s\n' "$file"
PLEXOS_SETUP
```

This creates a private credentials file at:

```text
~/.config/plexos-cloud/service-principal.env
```

The code handles special characters in your values and restricts file access to your Mac account. If you see **Credentials saved to …**, this step is complete.

## Ready for CLI authentication

Your credentials are now stored in a file that can be used when setting up the PLEXOS Cloud CLI in a Linux container on your Mac. The container will read this file during service-principal login.

## References

The official [Access Keys guide](https://docs.energyexemplar.com/plexos-cloud/central-license-manager-clm/access-keys-page) covers initial key generation, and the [CLI Toolkit guide](https://docs.energyexemplar.com/plexos-cloud/cli/cli-toolkit#id-6.1-login-via-service-principal) documents service-principal login.
