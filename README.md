
````markdown
# 🦅 Sherlook PasarGuard Host Manager

🇮🇷 **[فارسی](#فارسی)** &nbsp; | &nbsp; 🇬🇧 **[English](#english)**

---

<a name="فارسی"></a>

# 🇮🇷 راهنمای فارسی

## 🦅 Sherlook PasarGuard Host Manager

یک ابزار ترمینالی سریع و کاربردی برای مدیریت **Host**های پنل **PasarGuard** که با برند **Sherlook** توسعه داده شده است.

این ابزار برای ساده‌تر کردن مدیریت تعداد زیادی Host طراحی شده و امکاناتی مثل Duplicate، ساخت گروهی، شماره‌گذاری هوشمند و مرتب‌سازی Hostها را فراهم می‌کند.

---

## ✨ امکانات

### 📋 Duplicate کردن Host

امکان انتخاب یک یا چند Host برای ساخت نسخه‌های جدید.

می‌توانی انتخاب کنی:

```text
5
````

یا یک بازه:

```text
5-9
```

یا چند Host:

```text
5,7,9
```

و حتی ترکیبی:

```text
5-7,10,12-14
```

---

### ⚡ ساخت گروهی سریع

برای ساخت تعداد زیادی Host، ابزار از درخواست‌های Async با تعداد Worker محدود استفاده می‌کند.

به‌صورت پیش‌فرض:

```text
4 Worker همزمان
```

این کار باعث می‌شود ساخت تعداد زیادی Host نسبت به حالت کاملاً ترتیبی سریع‌تر باشد، بدون اینکه تعداد نامحدودی درخواست همزمان به پنل ارسال شود.

---

### 🔢 شماره‌گذاری هوشمند

Sherlook شماره Hostهای موجود را بررسی می‌کند و برای Hostهای جدید شماره مناسب را انتخاب می‌کند.

مثلاً اگر داشته باشیم:

```text
Germany 1
Germany 2
Germany 3
Germany 7
```

Host جدید از شماره بعدی مناسب استفاده می‌کند:

```text
Germany 8
```

همچنین شماره‌ها قبل از ساخت گروهی رزرو می‌شوند تا درخواست‌های همزمان باعث ایجاد نام تکراری نشوند.

---

### 🗂️ Group & Sort

Hostها بر اساس نام پایه گروه‌بندی و سپس به ترتیب عددی مرتب می‌شوند.

مثلاً:

```text
Spain 1
Spain 10
Spain 2
Germany 3
Germany 1
Germany 2
```

به شکل منطقی مرتب می‌شوند:

```text
Spain 1
Spain 2
Spain 10

Germany 1
Germany 2
Germany 3
```

قبل از اعمال تغییر، ترتیب پیشنهادی به کاربر نمایش داده می‌شود.

---

### 🔐 مدیریت اطلاعات ورود

در صورت انتخاب کاربر، اطلاعات ورود به‌صورت محلی ذخیره می‌شود:

```text
~/.sherlook_auth.json
```

فایل Credential با permission محدود `600` ایجاد می‌شود تا کاربران دیگر سیستم نتوانند به‌سادگی آن را بخوانند.

همچنین گزینه:

```text
Logout / Clear Saved Credentials
```

برای حذف اطلاعات ذخیره‌شده وجود دارد.

> ⚠️ توجه: اطلاعات ورود همچنان به‌صورت plaintext در فایل محلی ذخیره می‌شوند. بنابراین روی سیستم‌های اشتراکی یا غیرقابل اعتماد از Credential Cache استفاده نکنید.

---

### 🎨 رابط کاربری Sherlook

ابزار دارای رابط ترمینالی اختصاصی با:

* 🦅 لوگوی Sherlook
* 🎨 رنگ‌بندی ترمینال
* 📋 منوی ساده
* ⚡ نمایش وضعیت عملیات
* ❌ نمایش خطاها
* 🔢 نمایش تعداد Hostها

است.

---

### 🧩 نصب خودکار Dependency

اگر پکیج موردنیاز:

```text
pasarguard
```

روی سیستم نصب نباشد، برنامه به‌صورت خودکار تلاش می‌کند آن را نصب کند.

---

# 🚀 نصب و اجرا

## پیش‌نیازها

نیاز دارید به:

* Python 3.9 یا بالاتر
* دسترسی به پنل PasarGuard
* Username و Password معتبر
* دسترسی شبکه به پنل

بررسی نسخه Python:

```bash
python3 --version
```

اجرای برنامه:

```bash
python3 pasarguard_host_manager.py
```

در اولین اجرا، در صورت نبودن dependency، برنامه تلاش می‌کند پکیج `pasarguard` را نصب کند.

---

# 🖥️ نحوه استفاده

بعد از اجرای:

```bash
python3 pasarguard_host_manager.py
```

منوی اصلی نمایش داده می‌شود:

```text
==============================================================
Sherlook PasarGuard Host Manager
Active hosts: 25
==============================================================
  1) 📋 Duplicate host(s)
  2) 🔢 Sort / group hosts
  3) 👀 Show host list
  4) 🔐 Logout / clear saved credentials
  0) 🚪 Exit
```

---

## 1️⃣ Duplicate Host

گزینه:

```text
1
```

را انتخاب کنید.

سپس Host موردنظر را مشخص کنید:

```text
Host(s) to duplicate (e.g. 5 / 5-9 / 5,7,9): 5-9
```

و تعداد Copy را وارد کنید:

```text
Copies of EACH selected host: 3
```

Sherlook به‌صورت خودکار نام و شماره مناسب را انتخاب می‌کند و Hostها را ایجاد می‌کند.

---

## 2️⃣ Sort / Group Hosts

گزینه:

```text
2
```

را انتخاب کنید.

برنامه ترتیب پیشنهادی Hostها را نمایش می‌دهد.

مثلاً:

```text
  1) Germany 1
  2) Germany 2
  3) Germany 3
  4) Spain 1
  5) Spain 2
```

سپس قبل از ذخیره تغییرات از شما تأیید می‌گیرد.

---

## 3️⃣ Show Host List

گزینه:

```text
3
```

لیست Hostها را نمایش می‌دهد.

اطلاعاتی مانند:

```text
Remark
Inbound Tag
Address
Port
```

نمایش داده می‌شوند.

---

## 4️⃣ Logout

گزینه:

```text
4
```

اطلاعات ورود ذخیره‌شده را حذف می‌کند:

```text
~/.sherlook_auth.json
```

پس در اجرای بعدی باید دوباره اطلاعات ورود را وارد کنید.

---

# 🔒 نکات امنیتی

فایل زیر را **هرگز در GitHub Commit نکنید**:

```text
.sherlook_auth.json
```

پیشنهاد می‌شود فایل `.gitignore` شما شامل موارد زیر باشد:

```gitignore
.sherlook_auth.json
__pycache__/
*.pyc
.env
```

اگر اطلاعات ورود به‌صورت تصادفی وارد Repository عمومی شد، فوراً Password مربوط به پنل را تغییر دهید.

---

# 📁 ساختار پیشنهادی Repository

```text
multi/
│
├── sherlook.sh
├── pasarguard_host_manager.py
├── README.md
└── .gitignore
```

---

# ⚙️ تنظیم سرعت

تعداد Workerهای همزمان به‌صورت پیش‌فرض:

```python
MAX_CREATE_WORKERS = 4
```

است.

اگر سرور و پنل شما توانایی پردازش درخواست‌های بیشتری دارند، می‌توانید آن را افزایش دهید:

```python
MAX_CREATE_WORKERS = 6
```

یا:

```python
MAX_CREATE_WORKERS = 8
```

⚠️ افزایش بیش از حد Workerها همیشه باعث افزایش سرعت نمی‌شود و ممکن است باعث Rate Limit یا فشار روی API پنل شود.

---

# 🛠️ رفع مشکلات رایج

### خطای `ModuleNotFoundError`

اگر چنین خطایی دریافت کردید:

```text
ModuleNotFoundError: No module named 'pasarguard'
```

دستور زیر را اجرا کنید:

```bash
python3 -m pip install pasarguard
```

سپس:

```bash
python3 pasarguard_host_manager.py
```

---

### مشکل Login

اطمینان حاصل کنید:

```text
Panel URL
Username
Password
```

صحیح باشند.

مثال:

```text
https://panel.example.com:443
```

همچنین بررسی کنید سرور شما به پنل دسترسی شبکه داشته باشد.

---

### Sort روی پنل ذخیره نمی‌شود

برخی نسخه‌های PasarGuard API ممکن است فیلد قابل نوشتن `priority` را در مدل Host ارائه نکنند.

در این حالت برنامه ترتیب پیشنهادی را نمایش می‌دهد ولی وانمود نمی‌کند که تغییر روی پنل ذخیره شده است.

---

# 📜 License

این پروژه تحت مجوز:

```text
MIT License
```

منتشر شده است.

از این ابزار فقط برای مدیریت پنل‌ها و زیرساخت‌هایی استفاده کنید که مجوز مدیریت آن‌ها را دارید.

---

<p align="center">

# 🦅 Sherlook

### Simple Tools • Faster Workflows

Made with ❤️ for PasarGuard users.

</p>

---

<a name="english"></a>

# 🇬🇧 English Documentation

## 🦅 Sherlook PasarGuard Host Manager

A fast and practical terminal utility for managing **Host** entries on **PasarGuard** panels.

Developed under the **Sherlook** brand, the tool is designed to make large-scale host management easier with features such as duplication, bulk creation, smart numbering, grouping, and sorting.

---

# ✨ Features

## 📋 Host Duplication

Duplicate one or multiple hosts.

You can select:

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

## ⚡ Fast Bulk Creation

Bulk host creation uses bounded asynchronous workers.

Default configuration:

```text
4 concurrent workers
```

This allows multiple hosts to be created concurrently while avoiding an unlimited number of API requests against the panel.

---

## 🔢 Smart Numbering

Sherlook automatically analyzes existing host remarks and selects the next available number.

For example:

```text
Germany 1
Germany 2
Germany 3
Germany 7
```

A new host can automatically receive:

```text
Germany 8
```

During bulk creation, numbers are reserved before requests are sent, reducing the chance of duplicate names caused by concurrent requests.

---

## 🗂️ Smart Grouping & Sorting

Hosts are grouped by their base remark and sorted numerically.

Example:

```text
Spain 1
Spain 10
Spain 2
Germany 3
Germany 1
Germany 2
```

The proposed order becomes:

```text
Spain 1
Spain 2
Spain 10

Germany 1
Germany 2
Germany 3
```

The proposed order is shown before the application attempts to save changes.

---

## 🔐 Credential Management

If enabled, credentials are stored locally in:

```text
~/.sherlook_auth.json
```

The file is created with restrictive `600` permissions where supported by the operating system.

The application also provides:

```text
Logout / Clear Saved Credentials
```

to remove the saved credentials.

> ⚠️ **Security warning:** Credentials are still stored as plaintext locally. Do not enable credential caching on shared or untrusted machines.

---

## 🎨 Sherlook Terminal UI

The application includes a custom Sherlook terminal interface with:

* 🦅 Sherlook branding
* 🎨 Colored terminal output
* 📋 Simple interactive menu
* ⚡ Operation status
* ❌ Clear error messages
* 🔢 Active host counter

---

## 🧩 Automatic Dependency Installation

If the required:

```text
pasarguard
```

Python package is missing, the application automatically attempts to install it.

---

# 🚀 Installation

## Requirements

You need:

* Python 3.9+
* Access to a PasarGuard panel
* Valid PasarGuard credentials
* Network access to the panel

Check Python:

```bash
python3 --version
```

Run the application:

```bash
python3 pasarguard_host_manager.py
```

If the `pasarguard` package is missing, the application attempts to install it automatically.

---

# 🖥️ Usage

Start the application:

```bash
python3 pasarguard_host_manager.py
```

The main menu looks like:

```text
==============================================================
Sherlook PasarGuard Host Manager
Active hosts: 25
==============================================================
  1) 📋 Duplicate host(s)
  2) 🔢 Sort / group hosts
  3) 👀 Show host list
  4) 🔐 Logout / clear saved credentials
  0) 🚪 Exit
```

---

# 1️⃣ Duplicate Hosts

Select:

```text
1
```

Then choose the host(s):

```text
Host(s) to duplicate (e.g. 5 / 5-9 / 5,7,9): 5-9
```

Enter the number of copies:

```text
Copies of EACH selected host: 3
```

Sherlook automatically calculates suitable names and creates the new hosts.

---

# 2️⃣ Sort / Group Hosts

Select:

```text
2
```

The application displays the proposed host order.

Example:

```text
  1) Germany 1
  2) Germany 2
  3) Germany 3
  4) Spain 1
  5) Spain 2
```

The application asks for confirmation before attempting to save the order.

---

# 3️⃣ Show Host List

Select:

```text
3
```

The host list will display information such as:

```text
Remark
Inbound Tag
Address
Port
```

---

# 4️⃣ Logout

Select:

```text
4
```

This removes the saved local credentials:

```text
~/.sherlook_auth.json
```

The next time you run the application, you will need to enter your credentials again.

---

# 🔒 Security

Never commit the following file to GitHub:

```text
.sherlook_auth.json
```

Recommended `.gitignore`:

```gitignore
.sherlook_auth.json
__pycache__/
*.pyc
.env
```

If panel credentials are accidentally exposed in a public repository, immediately change the affected password.

---

# 📁 Recommended Repository Structure

```text
multi/
│
├── sherlook.sh
├── pasarguard_host_manager.py
├── README.md
└── .gitignore
```

---

# ⚙️ Performance Configuration

The default concurrent worker count is:

```python
MAX_CREATE_WORKERS = 4
```

If your server and PasarGuard panel can safely handle more concurrent API requests, you can increase it:

```python
MAX_CREATE_WORKERS = 6
```

or:

```python
MAX_CREATE_WORKERS = 8
```

⚠️ Increasing concurrency does not always make the process faster. Excessive concurrency may cause API rate limiting or unnecessary load on the panel.

---

# 🛠️ Troubleshooting

## `ModuleNotFoundError`

If you see:

```text
ModuleNotFoundError: No module named 'pasarguard'
```

Run:

```bash
python3 -m pip install pasarguard
```

Then:

```bash
python3 pasarguard_host_manager.py
```

---

## Login Problems

Verify:

```text
Panel URL
Username
Password
```

Example:

```text
https://panel.example.com:443
```

Also make sure that the server running Sherlook can reach the PasarGuard panel over the network.

---

## Sorting Cannot Be Saved

Some PasarGuard API versions may not expose a writable `priority` field on the Host model.

In that situation, Sherlook displays the proposed order but does not falsely report that the change was saved.

---

# 📜 License

This project is released under the:

```text
MIT License
```

Use this tool only to manage PasarGuard panels and infrastructure that you are authorized to administer.

---

<p align="center">

# 🦅 Sherlook

### Simple Tools • Faster Workflows

Made with ❤️ for PasarGuard users.

</p>

---

## ⭐ Support the Project

If Sherlook is useful to you, consider giving the repository a ⭐ on GitHub.

Contributions, bug reports, and improvements are welcome.

**Sherlook — Simple Tools • Faster Workflows.**

```

فقط همین را جایگزین کل `README.md` کن. بالای صفحه کاربر می‌تواند روی **🇮🇷 فارسی** یا **🇬🇧 English** بزند و مستقیماً به بخش مربوط به همان زبان برود.
```
