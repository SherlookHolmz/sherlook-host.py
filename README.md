# 🦅 Sherlook Host Manager

ابزار Sherlook Host Manager برای مدیریت سریع و ساده Hostهای پنل PasarGuard طراحی شده است.

این برنامه با رابط ترمینالی اختصاصی Sherlook، مدیریت Hostها، Duplicate، مرتب‌سازی و سایر عملیات را ساده‌تر می‌کند.

---

## 🚀 اسکریپت نصب

برای نصب کامل Sherlook Host Manager، Dependency موردنیاز و دستور `sherlook-host`، دستور زیر را روی سرور اجرا کنید:

```bash
bash <(wget -qO- https://raw.githubusercontent.com/SherlookHolmz/sherlook-host.py/main/install-sherlook-host.sh)
```

---

## ▶️ اجرای برنامه

بعد از نصب، برنامه را با دستور زیر اجرا کنید:

```bash
sherlook-host
```

اگر بعد از نصب دستور `sherlook-host` شناخته نشد:

```bash
source ~/.bashrc
```

سپس:

```bash
sherlook-host
```

---

## ✨ قابلیت‌ها

* 🦅 رابط کاربری اختصاصی Sherlook
* 🔐 اتصال به پنل PasarGuard
* 💾 ذخیره اطلاعات ورود برای استفاده‌های بعدی
* 🚪 Logout و حذف اطلاعات ورود ذخیره‌شده
* 📋 نمایش لیست Hostهای موجود
* 📑 Duplicate کردن Host
* 📦 Duplicate کردن چند Host به‌صورت هم‌زمان
* 🔢 انتخاب Host به‌صورت تکی، محدوده یا چند انتخاب
* ⚡ Duplicate کردن تمام Hostها
* 🧠 شماره‌گذاری و نام‌گذاری هوشمند Hostهای جدید
* 📊 مرتب‌سازی و Group کردن Hostها
* 🔄 Refresh کردن لیست Hostها
* 🛡️ Retry خودکار در درخواست‌های ناموفق
* 📦 نصب خودکار Dependency موردنیاز

---

## 📋 انتخاب Host

برای Duplicate کردن Host می‌توانید یک Host، چند Host یا یک محدوده را انتخاب کنید.

یک Host:

```text
5
```

یک محدوده:

```text
5-9
```

چند Host:

```text
5,7,9
```

---

## 📦 Duplicate همه Hostها

در منوی برنامه گزینه Duplicate All Hosts قرار دارد.

با استفاده از این گزینه می‌توانید تعداد Copy موردنظر را برای تمام Hostهای موجود ایجاد کنید.

---

## 🔢 نام‌گذاری هوشمند

هنگام Duplicate کردن Host، برنامه Hostهای موجود را بررسی می‌کند و شماره مناسب را برای Host جدید انتخاب می‌کند تا نام‌گذاری Hostها منظم باقی بماند.

---

## 📊 مرتب‌سازی Hostها

برنامه می‌تواند Hostها را بر اساس نام و شماره گروه‌بندی و مرتب کند.

قبل از اعمال تغییرات، ترتیب پیشنهادی نمایش داده می‌شود.

---

## 🔄 Refresh

در صورت ایجاد یا تغییر Host در پنل، می‌توانید از گزینه Refresh استفاده کنید تا لیست Hostها دوباره از پنل دریافت شود.

---

## 🔐 اطلاعات ورود

در صورت فعال کردن ذخیره اطلاعات ورود، اطلاعات موردنیاز به‌صورت محلی روی سرور ذخیره می‌شود تا در اجرای بعدی نیاز به وارد کردن مجدد اطلاعات نباشد.

اطلاعات ورود خود را در Repository عمومی GitHub قرار ندهید.

---

## 🖥️ اجرای دستی

در صورت تمایل می‌توانید برنامه را مستقیماً با Python اجرا کنید:

```bash
python3 sherlook-host.py
```

در صورت نصب نبودن Dependency:

```bash
python3 -m pip install pasarguard
```

---

## 📁 ساختار پروژه

```text
sherlook-host.py/
├── README.md
├── install-sherlook-host.sh
└── sherlook-host.py
```

---

## ⚡ نصب سریع

اگر فقط می‌خواهید برنامه را نصب کنید:

```bash
bash <(wget -qO- https://raw.githubusercontent.com/SherlookHolmz/sherlook-host.py/main/install-sherlook-host.sh)
```

بعد از نصب:

```bash
sherlook-host
```

---

## 🦅 Sherlook

Sherlook Host Manager یک ابزار مستقل برای مدیریت Hostهای PasarGuard است.

برای جلوگیری از تداخل با پروژه اصلی Sherlook، دستور این پروژه:

```text
sherlook-host
```

است.

دستور:

```text
sherlook
```

برای پروژه اصلی Sherlook استفاده می‌شود.

---

## ⚠️ توجه

این پروژه مخصوص مدیریت Hostهای PasarGuard است.

اطلاعات ورود پنل خود را در Repository عمومی GitHub قرار ندهید.
