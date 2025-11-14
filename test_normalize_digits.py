"""
تست تابع normalize_digits برای تبدیل اعداد فارسی و عربی به انگلیسی
"""

# تابع normalize_digits از services.py
def normalize_digits(text: str) -> str:
    """
    تبدیل اعداد فارسی (۰-۹) و عربی (٠-٩) به انگلیسی (0-9)
    """
    if not text:
        return text
    
    # اعداد فارسی
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    # اعداد عربی
    arabic_digits = '٠١٢٣٤٥٦٧٨٩'
    # اعداد انگلیسی
    english_digits = '0123456789'
    
    # ساخت جدول ترجمه
    translation_table = str.maketrans(
        persian_digits + arabic_digits,
        english_digits + english_digits
    )
    
    return text.translate(translation_table)


# تست‌ها
print("=" * 60)
print("تست تابع normalize_digits")
print("=" * 60)

# تست 1: تاریخ فارسی
test1 = "۱۴۰۳/۰۹/۱۵"
result1 = normalize_digits(test1)
print(f"✓ تاریخ فارسی: {test1} -> {result1}")
assert result1 == "1403/09/15", f"خطا! انتظار: 1403/09/15, نتیجه: {result1}"

# تست 2: کد ملی فارسی
test2 = "۱۲۳۴۵۶۷۸۹۰"
result2 = normalize_digits(test2)
print(f"✓ کد ملی فارسی: {test2} -> {result2}")
assert result2 == "1234567890", f"خطا! انتظار: 1234567890, نتیجه: {result2}"

# تست 3: ساعت فارسی
test3 = "۰۸:۰۰-۱۲:۰۰"
result3 = normalize_digits(test3)
print(f"✓ ساعت فارسی: {test3} -> {result3}")
assert result3 == "08:00-12:00", f"خطا! انتظار: 08:00-12:00, نتیجه: {result3}"

# تست 4: اعداد عربی
test4 = "٠١٢٣٤٥٦٧٨٩"
result4 = normalize_digits(test4)
print(f"✓ اعداد عربی: {test4} -> {result4}")
assert result4 == "0123456789", f"خطا! انتظار: 0123456789, نتیجه: {result4}"

# تست 5: ترکیبی فارسی و انگلیسی
test5 = "۱۴۰۳/09/15"
result5 = normalize_digits(test5)
print(f"✓ ترکیبی: {test5} -> {result5}")
assert result5 == "1403/09/15", f"خطا! انتظار: 1403/09/15, نتیجه: {result5}"

# تست 6: متن با اعداد فارسی
test6 = "کد پرسنلی: ۱۲۳۴۵"
result6 = normalize_digits(test6)
print(f"✓ متن با عدد: {test6} -> {result6}")
assert result6 == "کد پرسنلی: 12345", f"خطا! انتظار: 'کد پرسنلی: 12345', نتیجه: {result6}"

# تست 7: متن بدون عدد
test7 = "سلام علیکم"
result7 = normalize_digits(test7)
print(f"✓ متن بدون عدد: {test7} -> {result7}")
assert result7 == "سلام علیکم", f"خطا! انتظار: 'سلام علیکم', نتیجه: {result7}"

# تست 8: رشته خالی
test8 = ""
result8 = normalize_digits(test8)
print(f"✓ رشته خالی: '{test8}' -> '{result8}'")
assert result8 == "", f"خطا! انتظار: '', نتیجه: {result8}"

# تست 9: None
test9 = None
result9 = normalize_digits(test9)
print(f"✓ None: {test9} -> {result9}")
assert result9 is None, f"خطا! انتظار: None, نتیجه: {result9}"

# تست 10: تاریخ با خط تیره
test10 = "۱۴۰۳-۰۹-۱۵"
result10 = normalize_digits(test10)
print(f"✓ تاریخ با خط تیره: {test10} -> {result10}")
assert result10 == "1403-09-15", f"خطا! انتظار: 1403-09-15, نتیجه: {result10}"

print("=" * 60)
print("✅ همه تست‌ها با موفقیت انجام شد!")
print("=" * 60)
