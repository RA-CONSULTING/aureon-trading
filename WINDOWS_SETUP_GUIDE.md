# 🪟 Windows Setup Guide for Aureon Trading

It looks like you are setting up the system on a fresh Windows machine. Follow these steps exactly to get everything running.

## Step 1: Install Python
Your error `Python was not found` means Python is not installed.

1.  Open the **Microsoft Store** on your computer.
2.  Search for **"Python 3.11"**.
3.  Click **Get** or **Install**.
4.  **IMPORTANT**: When installing, if asked, check the box that says **"Add Python to PATH"**.

## Step 2: Open PowerShell Correctly
1.  Press `Win + X` and select **Windows PowerShell (Admin)** or **Terminal (Admin)**.
2.  You are currently in `C:\WINDOWS\system32`. You need to move to your project folder.

## Step 3: Navigate to the Folder
Type this command and press Enter:
```powershell
cd C:\Users\aureon-trading-main
```
*(If your folder name is different, replace `aureon-trading-main` with the correct name. You can type `cd C:\Users\` and press Tab to see available folders).*

## Step 4: Install Dependencies
Once you are inside the folder (your prompt should look like `PS C:\Users\aureon-trading-main>`), run:

```powershell
pip install -r requirements.txt
```

## Step 5: Run the System
Now you can start the ecosystem using the provided script:

```powershell
.\start_full_ecosystem.ps1
```

---

## Troubleshooting Common Errors

### "The term 'pip' is not recognized"
*   **Fix**: This means Python wasn't added to your PATH or you need to restart PowerShell after installing Python. Close the window and open it again.

### "The term 'git' is not recognized"
*   **Fix**: You don't strictly need Git if you downloaded the ZIP file. You can skip git commands.

### "Execution of scripts is disabled on this system"
*   **Fix**: If `.\start_full_ecosystem.ps1` fails, run this command first:
    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    ```
    Type `Y` when asked.
