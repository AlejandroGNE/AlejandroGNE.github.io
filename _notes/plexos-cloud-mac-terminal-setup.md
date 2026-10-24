---
title: "PLEXOS from Mac: Set Up a Terminal Workspace"
date: 2026-10-24
description: "Download the Linux CLI, build a Docker workspace on a Mac, and authenticate with service-principal credentials."
---

The PLEXOS Cloud CLI is distributed for Windows and Linux. On my Mac, I run the Linux version inside Docker and use service-principal credentials to log in without a browser.

This note starts with the credentials file prepared in [Set Up Service-Principal Credentials](/notes/plexos-cloud-service-principal-setup/) and ends with an authenticated Linux terminal where you can run `pxc` commands. No VS Code installation is needed.

## 1. Install Docker Desktop

Download [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/), choosing the version for your Mac's chip: **Apple silicon** or **Intel**. Install it, open Docker Desktop, and complete its first-run setup.

Open **Terminal** on your Mac and paste:

```bash
open -a Docker
docker info >/dev/null && echo "Docker is ready"
```

If Docker is still starting, wait until Docker Desktop says it is running, then repeat the second command.

## 2. Create the workspace

[Download the terminal setup files](/assets/plexos-cloud-mac-terminal-setup/plexos-mac-terminal-starter.zip) and save the ZIP in **Downloads**. These are the small launcher scripts and Dockerfile used in this note; the PLEXOS software is downloaded separately in the next step.

In **Mac Terminal**, paste this block:

```bash
mkdir -p "$HOME/Documents"
mkdir "$HOME/Documents/plexos-from-mac" &&
unzip -q "$HOME/Downloads/plexos-mac-terminal-starter.zip" \
  -d "$HOME/Documents/plexos-from-mac" &&
cd "$HOME/Documents/plexos-from-mac"
```

This creates a new folder at `Documents/plexos-from-mac`. If that folder already exists, use a different folder name or continue in your existing setup; the command deliberately stops rather than replacing it.

Keep this Terminal window open. All Mac commands below run from that folder.

## 3. Download the Linux CLI

Sign into PLEXOS Cloud in your Mac browser. Open the application grid, select **Marketplace**, then open **Tools**.

Find **PLEXOS Cloud Toolkit (Linux)** and select **DOWNLOAD**. Choose the Linux package even though you are using a Mac: the CLI will run inside Linux.

For my test, the Marketplace listed **1.5.2981.559**, released October 13, 2026. The CLI reports the shorter version **1.5.2981**. Use the current package offered for your environment and note its version.

With `CloudCLI-Linux-x64.zip` saved in Downloads, paste into **Mac Terminal**:

```bash
unzip -q "$HOME/Downloads/CloudCLI-Linux-x64.zip" -d cli
chmod +x cli/plexos-cloud
```

The executable should now be at `Documents/plexos-from-mac/cli/plexos-cloud`, alongside the rest of the package. Keep those files together. If the browser automatically extracted the ZIP, move the extracted package contents into `cli` instead, then run the `chmod` command.

This package is Linux x64. The Docker setup explicitly selects `linux/amd64`, including on Apple Silicon. The package I tested bundles .NET 10.0.8, so this setup does not install a separate .NET runtime.

## 4. Build the Linux image

In **Mac Terminal**, run:

```bash
./plexos build
```

This builds a Linux image called `plexos-mac-terminal:local` and installs the CLI's native dependencies. The first build downloads packages and can take a few minutes. Wait for the build to finish successfully before continuing.

The setup files also provide three commands inside Linux:

| Command | Purpose |
|---|---|
| `pxc` | Runs the PLEXOS Cloud CLI |
| `pxc-login` | Loads the credentials file and performs service-principal login |
| `pxc-check` | Checks the CLI version, authenticated status, and cloud environment |

`pxc-login` and `pxc-check` are helpers supplied with this note.

## 5. Open the Linux terminal

The launcher expects the credentials file created in the earlier note:

```text
~/.config/plexos-cloud/service-principal.env
```

In **Mac Terminal**, run:

```bash
./plexos shell
```

You are now **inside Linux**. The prompt will look similar to:

```text
root@...:/workspace#
```

The launcher connects these locations:

| Mac or Docker location | Inside Linux | Access |
|---|---|---|
| This workspace's `cli` folder | `/opt/plexos-cli` | Read-only |
| The credentials file | `/run/secrets/pxc.env` | Read-only |
| This workspace's `workspace` folder | `/workspace` | Read and write |
| Docker volume `plexos-mac-terminal-state` | `/root` | Stores the CLI session |

Save inputs and downloaded results under `/workspace`. They will be available in `Documents/plexos-from-mac/workspace` on your Mac.

## 6. Verify the CLI and choose the environment

Inside **Linux**, run:

```bash
pxc --version
pxc --help
pxc environment get
```

The first command should print the CLI version; the second should list its commands.

Check that the selected environment matches your PLEXOS Cloud tenant. If it needs changing, set it **before logging in**. For example, for North America:

```bash
pxc environment set NA
```

Use `EMEA` or `APAC` for those environments, or run the following to see the other supported values:

```bash
pxc environment set --help
```

Changing environments signs you out, so this is a setup step rather than something to repeat every day.

## 7. Authenticate

Still inside **Linux**, run:

```bash
pxc-login
pxc-check
```

The login helper reads the mounted file, loads its three credential variables, and calls `pxc auth login --service-principal`. You do not need to enter the secrets again or load them manually.

The check should show **Status: Authenticated**, the expected environment and tenant, and **CLI readiness check passed**.

You now have an authenticated CLI. Access to a particular study or operation will be checked when you use it.

## 8. Exit and reopen

Inside **Linux**, run:

```bash
exit
```

This returns you to **Mac Terminal**. Reopen the environment:

```bash
./plexos shell
```

Then, inside **Linux**, run:

```bash
pxc-check
```

The saved session should still be available. Each launch creates a fresh container, while the Docker volume retains the CLI's authentication state. If the login expires, run `pxc-login` again. Working files remain in the Mac workspace folder.

## Next time you open Terminal

Start Docker Desktop, then run these commands in **Mac Terminal**:

```bash
open -a Docker
cd "$HOME/Documents/plexos-from-mac"
./plexos shell
```

If Docker is still starting, wait and repeat `./plexos shell`. Once inside **Linux**:

```bash
pxc-check
```

If it asks you to authenticate:

```bash
pxc-login
pxc-check
```

You are ready to use `pxc` from the Linux prompt. Leave with `exit` when you are finished.

## If a setup step fails

| Symptom | Check |
|---|---|
| `docker` is not found | Finish installing Docker Desktop, then open a new Terminal window. |
| Cannot connect to Docker | Start Docker Desktop and wait until it is running. |
| Linux CLI is missing | Confirm `cli/plexos-cloud` exists directly inside the workspace and run `chmod +x cli/plexos-cloud`. |
| Credentials file is not found | Complete the [credentials setup](/notes/plexos-cloud-service-principal-setup/), or select an existing file using the command below. |
| Login fails | Confirm the selected environment and that the credentials file contains all three values. |

For an existing credentials file at a different location, use its absolute path when opening Linux:

```bash
PXC_ENV_FILE="/absolute/path/to/credentials.env" ./plexos shell
```

Run one session at a time. Keep the CLI package read-only in the container; download future CLI updates on the Mac. Rebuilding the image preserves the saved session volume and working files.

## References

- [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
- [PLEXOS Cloud CLI Toolkit](https://docs.energyexemplar.com/plexos-cloud/cli/cli-toolkit)

The terminal workflow was tested on an Apple Silicon Mac with the Linux Toolkit version recorded above. Installing Docker Desktop on a clean Mac and Intel Mac execution were not part of that test. This note sets up the CLI; simulation execution takes place in PLEXOS Cloud.
