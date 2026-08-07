
````markdown
# 🦅 Sherlook

🇮🇷 **[فارسی](#فارسی)** &nbsp; | &nbsp; 🇬🇧 **[English](#english)**

---

<a name="فارسی"></a>

# 🇮🇷 راهنمای فارسی

## 🦅 Sherlook

Sherlook یک مجموعه ابزار ترمینالی برای مدیریت سرویس‌ها و ابزارهای مرتبط با **PasarGuard** و مدیریت Location است.

هدف پروژه این است که ابزارهای Sherlook را در یک محیط ساده، سریع و قابل استفاده از طریق یک دستور در اختیار کاربر قرار دهد.

---

# 🚀 نصب آسان

برای نصب کامل Sherlook، شامل:

- 🌍 `sherlook.sh`
- 📋 `pasarguard_host_manager.py`
- 🚀 دستور `sherlook`

فقط دستور زیر را اجرا کنید:

```bash
bash <(wget -qO- https://raw.githubusercontent.com/SherlookHolmz/multi/main/install-sherlook.sh)
````

Installer به‌صورت خودکار فایل‌های موردنیاز را دانلود و نصب می‌کند.

پس از نصب، فقط کافی است:

```bash
sherlook
```

را اجرا کنید.

---

# 🦅 منوی اصلی Sherlook

بعد از اجرای:

```bash
sherlook
```

منوی اصلی نمایش داده می‌شود:

```text
🦅 Sherlook

Select tool:

  1) 🌍 Sherlook Location Manager
  2) 📋 PasarGuard Host Manager
  0) 🚪 Exit

>
```

### گزینه 1 — 🌍 Sherlook Location Manager

این گزینه `sherlook.sh` را اجرا می‌کند و ابزار مدیریت Locationهای Sherlook را در اختیار شما قرار می‌دهد.

### گزینه 2 — 📋 PasarGuard Host Manager

این گزینه ابزار مدیریت Hostهای PasarGuard را اجرا می‌کند.

### گزینه 0 — 🚪 Exit

خروج از منوی Sherlook.

---

# 📦 فایل‌های پروژه

ساختار Repository:

```text
multi/
│
├── sherlook.sh
├── pasarguard_host_manager.py
├── install-sherlook.sh
├── README.md
└── .gitignore
```

---

# 🌍 Sherlook Location Manager

فایل:

```text
sherlook.sh
```

ابزار اصلی مدیریت Locationهای Sherlook است.

برای اجرای مستقیم:

```bash
bash sherlook.sh
```

یا پس از نصب:

```bash
sherlook
```

و سپس گزینه:

```text
1) 🌍 Sherlook Location Manager
```

را انتخاب کنید.

---

# 📋 PasarGuard Host Manager

فایل:

```text
pasarguard_host_manager.py
```

برای مدیریت Hostهای PasarGuard طراحی شده است.

امکانات:

* 📋 Duplicate Host
* ⚡ Bulk Host Creation
* 🔢 Smart Numbering
* 🗂️ Group & Sort
* 🔐 Local Credential Cache
* 🎨 رابط ترمینالی Sherlook
* 🔁 Retry برای درخواست‌های ناموفق
* ⚡ ساخت همزمان با Async Worker

اجرای مستقیم:

```bash
python3 pasarguard_host_manager.py
```

یا از طریق:

```bash
sherlook
```

گزینه:

```text
2) 📋 PasarGuard Host Manager
```

را انتخاب کنید.

---

# 📋 Duplicate Host

امکان انتخاب یک یا چند Host وجود دارد.

یک Host:

```text
5
```

یک بازه:

```text
5-9
```

چند Host:

```text
5,7,9
```

ترکیبی:

```text
5-7,10,12-14
```

---

# ⚡ Bulk Creation

ساخت Hostهای متعدد با Async Worker انجام می‌شود.

تعداد پیش‌فرض Worker:

```python
MAX_CREATE_WORKERS = 4
```

این مقدار قابل تغییر است.

مثلاً:

```python
MAX_CREATE_WORKERS = 6
```

یا:

```python
MAX_CREATE_WORKERS = 8
```

⚠️ افزایش بیش از حد Workerها ممکن است باعث فشار روی API یا Rate Limit پنل شود.

---

# 🔢 Smart Numbering

Sherlook شماره‌های موجود را بررسی می‌کند و شماره مناسب بعدی را برای Host جدید انتخاب می‌کند.

مثلاً:

```text
Germany 1
Germany 2
Germany 3
Germany 7
```

Host جدید:

```text
Germany 8
```

در عملیات Bulk، شماره‌ها قبل از ارسال درخواست‌ها رزرو می‌شوند تا درخواست‌های همزمان باعث ایجاد شماره تکراری نشوند.

---

# 🗂️ Group & Sort

Hostها بر اساس Base Name گروه‌بندی و سپس عددی مرتب می‌شوند.

مثلاً:

```text
Spain 1
Spain 10
Spain 2

Germany 3
Germany 1
Germany 2
```

به:

```text
Spain 1
Spain 2
Spain 10

Germany 1
Germany 2
Germany 3
```

تبدیل می‌شوند.

قبل از ذخیره، ترتیب پیشنهادی نمایش داده می‌شود.

---

# 🔐 Credential Cache

در صورت فعال کردن ذخیره اطلاعات ورود، فایل زیر ایجاد می‌شود:

```text
~/.sherlook_auth.json
```

فایل با permission محدود `600` ایجاد می‌شود.

برای حذف اطلاعات ذخیره‌شده از:

```text
Logout / Clear Saved Credentials
```

استفاده کنید.

⚠️ اطلاعات ورود به‌صورت plaintext در فایل محلی ذخیره می‌شوند. روی سیستم‌های اشتراکی یا غیرقابل اعتماد Credential Cache را فعال نکنید.

---

# 🧩 نصب Dependency

PasarGuard Host Manager در صورت نبودن پکیج موردنیاز، تلاش می‌کند dependency مربوط به:

```text
pasarguard
```

را به‌صورت خودکار نصب کند.

---

# 🛠️ به‌روزرسانی Sherlook

برای دریافت نسخه جدید، Installer را دوباره اجرا کنید:

```bash
bash <(wget -qO- https://raw.githubusercontent.com/SherlookHolmz/multi/main/install-sherlook.sh)
```

Installer فایل‌های جدید را دریافت کرده و نسخه موجود را به‌روزرسانی می‌کند.

---

# 🔒 نکات امنیتی

فایل زیر را هرگز در GitHub قرار ندهید:

```text
.sherlook_auth.json
```

پیشنهاد می‌شود `.gitignore` شامل موارد زیر باشد:

```gitignore
.sherlook_auth.json
__pycache__/
*.pyc
.env
```

اگر اطلاعات ورود به‌صورت تصادفی در Repository عمومی قرار گرفت، Password مربوط به پنل را فوراً تغییر دهید.

---

# 📁 محل نصب

Installer فایل‌های Sherlook را در:

```text
~/.sherlook/
```

قرار می‌دهد.

ساختار نصب:

```text
~/.sherlook/
│
├── sherlook.sh
├── pasarguard_host_manager.py
└── VERSION
```

دستور اصلی:

```text
~/bin/sherlook
```

قرار می‌گیرد.

Installer در صورت نیاز `~/bin` را به `PATH` اضافه می‌کند.

---

# 🚀 اجرای سریع

بعد از نصب:

```bash
sherlook
```

همه‌چیز از طریق همین دستور قابل دسترسی است.

---

# 🛠️ Troubleshooting

## `sherlook: command not found`

اگر بلافاصله بعد از نصب دستور `sherlook` شناخته نشد، ترمینال را باز و بسته کنید یا اجرا کنید:

برای Bash:

```bash
source ~/.bashrc
```

برای Zsh:

```bash
source ~/.zshrc
```

سپس:

```bash
sherlook
```

---

## Python پیدا نمی‌شود

برای PasarGuard Host Manager به Python نیاز است.

بررسی:

```bash
python3 --version
```

---

## خطای PasarGuard Package

در صورت نیاز:

```bash
python3 -m pip install pasarguard
```

---

# 📜 License

این پروژه تحت:

```text
MIT License
```

منتشر شده است.

از Sherlook فقط برای سیستم‌ها، سرورها و پنل‌هایی استفاده کنید که مجوز مدیریت آن‌ها را دارید.

---

<p align="center">

# 🦅 Sherlook

### Simple Tools • Faster Workflows

Made with ❤️ for PasarGuard users.

</p>

---

<a name="english"></a>

# 🇬🇧 English Documentation

## 🦅 Sherlook

Sherlook is a collection of terminal utilities for managing **PasarGuard-related services** and Sherlook Location tools.

The project is designed to provide the available Sherlook tools through a simple, fast, and unified terminal command.

---

# 🚀 Easy Installation

To install the complete Sherlook package, including:

* 🌍 `sherlook.sh`
* 📋 `pasarguard_host_manager.py`
* 🚀 the `sherlook` command

run:

```bash
bash <(wget -qO- https://raw.githubusercontent.com/SherlookHolmz/multi/main/install-sherlook.sh)
```

The installer automatically downloads and installs the required Sherlook files.

After installation, simply run:

```bash
sherlook
```

---

# 🦅 Sherlook Main Menu

After running:

```bash
sherlook
```

you will see:

```text
🦅 Sherlook

Select tool:

  1) 🌍 Sherlook Location Manager
  2) 📋 PasarGuard Host Manager
  0) 🚪 Exit

>
```

### Option 1 — 🌍 Sherlook Location Manager

Launches:

```text
sherlook.sh
```

and opens the Sherlook Location Manager.

### Option 2 — 📋 PasarGuard Host Manager

Launches:

```text
pasarguard_host_manager.py
```

for PasarGuard host management.

### Option 0 — 🚪 Exit

Exit the Sherlook menu.

---

# 📦 Repository Structure

```text
multi/
│
├── sherlook.sh
├── pasarguard_host_manager.py
├── install-sherlook.sh
├── README.md
└── .gitignore
```

---

# 🌍 Sherlook Location Manager

File:

```text
sherlook.sh
```

This is the main Sherlook Location Manager.

Run directly:

```bash
bash sherlook.sh
```

Or after installation:

```bash
sherlook
```

and select:

```text
1) 🌍 Sherlook Location Manager
```

---

# 📋 PasarGuard Host Manager

File:

```text
pasarguard_host_manager.py
```

A terminal utility for managing PasarGuard hosts.

Features include:

* 📋 Host duplication
* ⚡ Bulk host creation
* 🔢 Smart numbering
* 🗂️ Group & sort
* 🔐 Local credential cache
* 🎨 Sherlook terminal UI
* 🔁 Retry handling
* ⚡ Async worker-based creation

Run directly:

```bash
python3 pasarguard_host_manager.py
```

Or run:

```bash
sherlook
```

and select:

```text
2) 📋 PasarGuard Host Manager
```

---

# 📋 Host Duplication

You can select a single host:

```text
5
```

A range:

```text
5-9
```

Multiple hosts:

```text
5,7,9
```

Or a combination:

```text
5-7,10,12-14
```

---

# ⚡ Bulk Creation

Multiple hosts are created using bounded asynchronous workers.

Default:

```python
MAX_CREATE_WORKERS = 4
```

This can be increased if your panel can safely handle more concurrent API requests.

For example:

```python
MAX_CREATE_WORKERS = 6
```

or:

```python
MAX_CREATE_WORKERS = 8
```

⚠️ Excessive concurrency may cause API rate limiting or unnecessary load on the panel.

---

# 🔢 Smart Numbering

Sherlook analyzes existing host remarks and selects the next available number.

Example:

```text
Germany 1
Germany 2
Germany 3
Germany 7
```

New host:

```text
Germany 8
```

During bulk operations, numbers are reserved before API requests are sent to reduce naming collisions.

---

# 🗂️ Group & Sort

Hosts are grouped by their base name and sorted numerically.

Example:

```text
Spain 1
Spain 10
Spain 2

Germany 3
Germany 1
Germany 2
```

Becomes:

```text
Spain 1
Spain 2
Spain 10

Germany 1
Germany 2
Germany 3
```

The proposed order is displayed before changes are saved.

---

# 🔐 Credential Cache

When enabled, credentials are stored locally in:

```text
~/.sherlook_auth.json
```

The file is created with restrictive `600` permissions where supported.

Use:

```text
Logout / Clear Saved Credentials
```

to remove the stored credentials.

⚠️ Credentials are stored as plaintext locally. Do not enable credential caching on shared or untrusted machines.

---

# 🧩 Automatic Dependency Installation

If the required Python package:

```text
pasarguard
```

is missing, the PasarGuard Host Manager attempts to install it automatically.

---

# 🛠️ Updating Sherlook

To download the latest version, run the installer again:

```bash
bash <(wget -qO- https://raw.githubusercontent.com/SherlookHolmz/multi/main/install-sherlook.sh)
```

The installer downloads the latest files and updates the existing installation.

---

# 🔒 Security

Never commit:

```text
.sherlook_auth.json
```

to GitHub.

Recommended `.gitignore`:

```gitignore
.sherlook_auth.json
__pycache__/
*.pyc
.env
```

If credentials are accidentally exposed in a public repository, immediately change the affected panel password.

---

# 📁 Installation Location

The installer stores Sherlook files in:

```text
~/.sherlook/
```

Installation structure:

```text
~/.sherlook/
│
├── sherlook.sh
├── pasarguard_host_manager.py
└── VERSION
```

The main launcher is installed as:

```text
~/bin/sherlook
```

The installer adds `~/bin` to `PATH` when necessary.

---

# 🚀 Quick Start

After installation:

```bash
sherlook
```

All installed Sherlook tools can be accessed through this command.

---

# 🛠️ Troubleshooting

## `sherlook: command not found`

If the command is not immediately available after installation, reload your shell.

For Bash:

```bash
source ~/.bashrc
```

For Zsh:

```bash
source ~/.zshrc
```

Then:

```bash
sherlook
```

---

## Python Not Found

Python is required for the PasarGuard Host Manager.

Check:

```bash
python3 --version
```

---

## PasarGuard Package Error

If necessary:

```bash
python3 -m pip install pasarguard
```

---

# 📜 License

This project is released under the:

```text
MIT License
```

Use Sherlook only on systems, servers, and panels that you are authorized to administer.

---

<p align="center">

# 🦅 Sherlook

### Simple Tools • Faster Workflows

Made with ❤️ for PasarGuard users.

</p>

---

## ⭐ Support

If Sherlook is useful to you, consider giving the GitHub repository a ⭐.

Bug reports, suggestions, and improvements are welcome.

**Sherlook — Simple Tools • Faster Workflows.**

```

**نکته:** در این نسخه `install-sherlook.sh` هم رسماً داخل README معرفی شده و نصب آسان، دستور `sherlook`، هر دو ابزار و ساختار نهایی Repository همگی با Installer جدید هماهنگ شده‌اند.
```
