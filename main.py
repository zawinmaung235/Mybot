import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Helper Functions
def get_digit_sum(num_str):
    clean_str = ''.join(filter(str.isdigit, str(num_str)))
    if not clean_str:
        return 0
    s = sum(int(d) for d in clean_str)
    while s >= 10:
        s = sum(int(d) for d in str(s))
    return s

def get_power_value(digit):
    return (digit + 5) % 10

def calculate_2d(index_str, value_str, last_str):
    index_val = float(index_str)
    value_val = float(value_str)
    last_num = int(last_str)

    # ----------------------------------------------------
    # 1. Session Split Calculation
    # ----------------------------------------------------
    index_dec = round((index_val % 1) * 100)
    value_dec = round((value_val % 1) * 100)
    diff = abs(index_dec - value_dec)

    core_base = diff % 10
    power_pair = (core_base + 5) % 10

    raw_set = set([core_base, power_pair])

    last_first_digit = last_num // 10
    last_second_digit = last_num % 10

    raw_set.add((last_first_digit + 3) % 10)
    raw_set.add((last_second_digit + 3) % 10)

    counter = 0
    while len(raw_set) < 4:
        raw_set.add((core_base + counter) % 10)
        counter += 1

    main_matrix = list(raw_set)[:4]
    buffer_digit = (main_matrix[0] + 2) % 10
    if buffer_digit in main_matrix:
        buffer_digit = (buffer_digit + 5) % 10

    main_pairs = []
    double_pairs = []
    for i in range(len(main_matrix)):
        double_pairs.append(f"{main_matrix[i]}{main_matrix[i]}")
        for j in range(i + 1, len(main_matrix)):
            main_pairs.append(f"{main_matrix[i]}{main_matrix[j]}")

    # ----------------------------------------------------
    # 2. Daily Precision Calculation
    # ----------------------------------------------------
    delta_daily = abs(index_dec - value_dec)
    main_anchor_digit = delta_daily % 10
    power_digit = (main_anchor_digit + 5) % 10

    # ----------------------------------------------------
    # 3. Decimal Shift Matrix V3.0 Calculation
    # ----------------------------------------------------
    idx_parts = index_str.split('.')
    val_parts = value_str.split('.')
    index_decimal_str = idx_parts[1] if len(idx_parts) > 1 else '0'
    value_decimal_str = val_parts[1] if len(val_parts) > 1 else '0'

    index_dec_sum = get_digit_sum(index_decimal_str)
    value_dec_sum = get_digit_sum(value_decimal_str)
    dec_diff = abs(index_dec_sum - value_dec_sum)
    power_synergy = get_digit_sum(index_dec_sum + value_dec_sum)

    h1 = int(str(last_str)[0])
    h2 = int(str(last_str)[1])
    sum2d = get_digit_sum(h1 + h2)

    cross1 = get_digit_sum(sum2d + dec_diff)
    cross2 = abs(sum2d - dec_diff)

    index_whole = int(index_val)
    index_whole_sum = get_digit_sum(index_whole)

    main_head = get_digit_sum(cross1 + index_whole_sum)
    sub_head = get_digit_sum(cross2 + index_whole_sum)

    if h1 == h2:
        main_head = get_digit_sum(power_synergy - h1 + 10)
        sub_head = get_digit_sum(main_head + 3)

    power_head = get_power_value(main_head)
    if sub_head == main_head or sub_head == power_head:
        sub_head = get_power_value(sub_head + 1)

    # Output Formatting
    result_text = (
        "📊 *3-in-1 2D Analysis Dashboard*\n\n"
        "1️⃣ *Session Split Matrix*\n"
        f"• Main Matrix (၄ လုံးခွေ): `{ ' - '.join(map(str, main_matrix)) }`\n"
        f"• Buffer Digit (ကပ်လွဲ): `+{buffer_digit}`\n"
        f"• အဓိက ဂဏန်းတွဲများ: `{ ', '.join(main_pairs) }`\n"
        f"• အပူးဂဏန်းများ: `{ ', '.join(double_pairs) }`\n\n"
        "2️⃣ *Daily Precision (မိန်း ၁ ကွက်)*\n"
        f"• မိန်း ပတ်သီး (Main Anchor): `{main_anchor_digit}`\n"
        f"• ရက်အလိုက် တစ်ကွက်ကောင်း: `{main_anchor_digit}{power_digit}` (R - `{power_digit}{main_anchor_digit}`)\n\n"
        "3️⃣ *Decimal Shift Matrix V3.0*\n"
        f"• အဓိက ထိပ်: `{main_head}`\n"
        f"• ပါဝါ ထိပ်: `{power_head}`\n"
        f"• အရံ ထိပ်: `{sub_head}`\n"
    )
    return result_text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "👋 မင်္ဂလာပါ! 3-in-1 2D Analysis Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "တွက်ချက်လိုသော ကိန်းဂဏန်းများကို အောက်ပါ format အတိုင်း ပို့ပေးပါ:\n\n"
        "`SET_Index SET_Value ထွက်ဂဏန်း`\n\n"
        "ဥပမာ -\n`1588.82 35776.44 26`"
    )
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().split()
    if len(text) != 3:
        await update.message.reply_text(
            "⚠️ Format မှားယွင်းနေပါသည်။\n\nဥပမာအတိုင်း ခြားပြီး ရိုက်ထည့်ပေးပါ:\n`1588.82 35776.44 26`",
            parse_mode='Markdown'
        )
        return

    try:
        index_str, value_str, last_str = text[0], text[1], text[2]
        
        # Validation
        float(index_str)
        float(value_str)
        if len(last_str) != 2 or not last_str.isdigit():
            raise ValueError()

        response = calculate_2d(index_str, value_str, last_str)
        await update.message.reply_text(response, parse_mode='Markdown')

    except ValueError:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ မှန်ကန်သော ကိန်းဂဏန်းများကိုသာ ဖြည့်သွင်းပေးပါ။\n(ဥပမာ - `1588.82 35776.44 26`)", parse_mode='Markdown')

def main():
    # Railway (သို့) Server ၏ Environment Variable မှ TOKEN ကို ယူမည်
    TOKEN = os.environ.get("TOKEN")
    
    if not TOKEN:
        print("Error: TOKEN environment variable is not set!")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
