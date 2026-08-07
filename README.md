# 🦅 Sherlook

مجموعه ابزارهای Sherlook برای مدیریت ساده، سریع و حرفه‌ای سرورها و پنل PasarGuard.

---

## 🚀 نصب آسان

برای نصب کامل Sherlook شامل:

* 🌍 Sherlook Location Manager
* 📋 PasarGuard Host Manager
* ⚡ دستور `sherlook`
* 🔧 نصب خودکار وابستگی‌های موردنیاز
* 🔄 امکان به‌روزرسانی

## 📥 اسکریپت نصب

```bash
bash <(wget -qO- https://raw.githubusercontent.com/SherlookHolmz/multi/main/install-sherlook.sh)
```

---

## 🦅 اجرای برنامه

بعد از نصب:

```bash
sherlook
```

منوی اصلی:

```text
🦅 Sherlook

Select tool:

  1) 🌍 Sherlook Location Manager
  2) 📋 PasarGuard Host Manager
  0) 🚪 Exit
```

---

## 🌍 Sherlook Location Manager

با انتخاب گزینه ۱، ابزار اصلی مدیریت Locationهای Sherlook اجرا می‌شود.

فایل اصلی:

```text
sherlook.sh
```

اجرای مستقیم:

```bash
bash sherlook.sh
```

---

## 📋 PasarGuard Host Manager

با انتخاب گزینه ۲، ابزار مدیریت Hostهای PasarGuard اجرا می‌شود.

فایل اصلی:

```text
pasarguard_host_manager.py
```

### امکانات

* 📋 Duplicate کردن Host
* ⚡ ساخت گروهی Host
* 🔢 شماره‌گذاری هوشمند
* 🗂️ گروه‌بندی Hostها
* ↕️ مرتب‌سازی Hostها
* 🚀 ساخت همزمان Hostها
* 🔐 ذخیره اختیاری اطلاعات ورود
* 🎨 رابط ترمینالی اختصاصی Sherlook

---

## 📋 انتخاب Host

امکان انتخاب یک Host:

```text
5
```

بازه‌ای از Hostها:

```text
5-9
```

چند Host:

```text
5,7,9
```

انتخاب ترکیبی:

```text
5-7,10,12-14
```

---

## 🔢 شماره‌گذاری هوشمند

Sherlook Hostهای موجود را بررسی کرده و شماره مناسب بعدی را انتخاب می‌کند.

مثلاً:

```text
Germany 1
Germany 2
Germany 3
Germany 7
```

Host بعدی:

```text
Germany 8
```

---

## ⚡ ساخت گروهی

ساخت چندین Host با Workerهای همزمان انجام می‌شود تا عملیات سریع‌تر انجام شود.

مقدار پیش‌فرض:

```python
MAX_CREATE_WORKERS = 4
```

در صورت نیاز می‌توان تعداد Workerها را افزایش داد.

---

## 🗂️ مرتب‌سازی Hostها

Hostها بر اساس نام و شماره مرتب می‌شوند.

مثلاً:

```text
Spain 1
Spain 10
Spain 2
```

به:

```text
Spain 1
Spain 2
Spain 10
```

تبدیل می‌شوند.

---

## 🔐 اطلاعات ورود

در صورت فعال کردن ذخیره اطلاعات ورود، اطلاعات به‌صورت محلی در فایل زیر ذخیره می‌شود:

```text
~/.sherlook_auth.json
```

برای حذف اطلاعات ذخیره‌شده می‌توانید از گزینه Logout استفاده کنید.

این فایل نباید در GitHub قرار بگیرد.

---

## 📁 محل نصب

Installer فایل‌های Sherlook را در مسیر زیر قرار می‌دهد:

```text
~/.sherlook/
```

ساختار:

```text
~/.sherlook/
├── sherlook.sh
├── pasarguard_host_manager.py
└── VERSION
```

دستور اصلی:

```text
~/bin/sherlook
```

---

## 🔄 به‌روزرسانی

برای دریافت آخرین نسخه، اسکریپت نصب را دوباره اجرا کنید.

```bash
bash <(wget -qO- https://raw.githubusercontent.com/SherlookHolmz/multi/main/install-sherlook.sh)
```

---

## 🧩 نیازمندی‌ها

* Linux
* Bash
* Python 3
* wget
* دسترسی شبکه

PasarGuard Host Manager در صورت نیاز dependency مربوط به `pasarguard` را به‌صورت خودکار نصب می‌کند.

---

## 🛠️ رفع مشکل

اگر دستور `sherlook` شناخته نشد:

```bash
source ~/.bashrc
```

سپس:

```bash
sherlook
```

---

## 🔒 امنیت

فایل زیر را در Repository عمومی قرار ندهید:

```text
.sherlook_auth.json
```

پیشنهاد می‌شود `.gitignore` شامل موارد زیر باشد:

```text
.sherlook_auth.json
__pycache__/
*.pyc
.env
```

---

## 📦 ساختار Repository

```text
multi/
├── sherlook.sh
├── pasarguard_host_manager.py
├── install-sherlook.sh
├── README.md
└── .gitignore
```

---

## 📜 مجوز

این پروژه تحت مجوز MIT منتشر شده است.

لطفاً از Sherlook فقط برای مدیریت سرورها و پنل‌هایی استفاده کنید که مجوز مدیریت آن‌ها را دارید.

---

<div align="center">

🦅 **Sherlook**

Simple Tools • Faster Workflows

</div>
