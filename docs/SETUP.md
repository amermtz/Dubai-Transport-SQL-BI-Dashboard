# Setup

One-time environment setup. Work top to bottom; each section ends with a verification step.

---

## ⚠️ Read this first: how MySQL and Tableau Public fit together

**Tableau Public Desktop (the free edition) connects only to file-based sources** —
Excel, CSV/text, JSON, PDF, spatial and statistical files, Google Sheets. **It does not
ship the MySQL connector** that paid Tableau Desktop has. *(Verify this yourself on the
connect pane after installing — if a MySQL option is present, great, use it directly.)*

That is not a problem, and it does not weaken the project. The architecture is:

```
data/raw/*.csv  ──load.py──>  MySQL  ──queries.sql──>  data/processed/*.csv  ──>  Tableau Public
   (source)                (modelling +              (query results,            (visualisation)
                            analysis layer)           analysis-ready)
```

MySQL still does all the real work — schema design, joins, aggregation, the analysis
itself. Tableau reads the *results*. This is a normal, defensible BI pattern, and the
brief explicitly allows it ("connect the BI tool to the data **or to a cleaned export**").

**Be able to say this out loud in an interview.** "I modelled and analysed in MySQL and
published the query outputs to Tableau" is a perfectly strong answer. Claiming a live
database connection you don't have is not.

---

## 1. MySQL Server

### Install

Option A — winget (simplest):

```powershell
winget install Oracle.MySQL
```

Option B — installer: download the **MySQL Installer for Windows** from
<https://dev.mysql.com/downloads/installer/> and choose the *Server only* or
*Developer Default* setup type.

During setup:
- Choose **"Use Strong Password Encryption"**.
- **Set a root password and save it somewhere you will not lose it.** You need it every
  session, and there is no easy recovery.
- Leave the port at the default **3306**.
- Let it install MySQL as a Windows service that starts automatically.

Optionally also install **MySQL Workbench** — a GUI for browsing tables and, usefully
here, for **auto-generating the ER diagram** (Database → Reverse Engineer) that the
README needs.

### Verify

```powershell
mysql --version
mysql -u root -p -e "SELECT VERSION();"
```

If `mysql` is not recognised, its `bin` folder is not on your PATH. Add
`C:\Program Files\MySQL\MySQL Server 8.4\bin` (adjust the version) to your user PATH,
then open a new terminal.

### Create the database

```powershell
mysql -u root -p -e "CREATE DATABASE dubai_transport CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

`utf8mb4` matters — Dubai datasets frequently carry Arabic place names, and the older
`utf8` alias will mangle them.

### Store credentials (never commit these)

Create a `.env` file in the project root:

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=dubai_transport
```

`.env` is already in `.gitignore`. `.env.example` documents the shape without the secret
and *is* committed.

---

## 2. Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks the activation script:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Verify:

```powershell
python -c "import pandas, sqlalchemy, pymysql; print('ok')"
```

---

## 3. Tableau Public

1. Create a free account at <https://public.tableau.com> — **the account is the
   deliverable**, since your published dashboard lives at a URL under your profile.
2. Download and install **Tableau Desktop Public Edition** from the same site.
3. Sign in inside the app (File → Sign In) so publishing works later.

### Know this before you build

- **Everything you publish is public.** That is the point here, but never load anything
  confidential into Tableau Public.
- Tableau Public **cannot save workbooks locally in the normal way** — saving means
  publishing to your online profile. Plan to publish an early rough version and
  overwrite it as you iterate; don't expect to work privately and publish once at the end.
- Once published, grab the URL — it goes at the top of the README and on your CV.

---

## Setup checklist

- [ ] MySQL installed, `mysql --version` works, root password saved
- [ ] `dubai_transport` database created with utf8mb4
- [ ] `.env` created with real credentials
- [ ] Python venv created, `requirements.txt` installed
- [ ] Tableau Public account created and Desktop Public Edition installed + signed in
- [ ] Data downloaded into `data/raw/` — see [DATA-SOURCING.md](DATA-SOURCING.md)
