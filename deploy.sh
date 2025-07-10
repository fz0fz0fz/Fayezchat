#!/bin/bash

# سكربت لتحديث المشروع ورفعه إلى GitHub بضغطة واحدة

echo "🚀 ابدأ التحديث"
echo "💬 اكتب رسالة التحديث (مثلاً: تعديل الرد على الصيدليات):"
read message

# أوامر Git
git add .
git commit -m "$message"
git push origin main

echo "✅ تم رفع التحديث إلى GitHub بنجاح"
