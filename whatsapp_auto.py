import os
import time
from datetime import datetime
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException


# ---------- LOGGING ----------
def log_result(status, number, details=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs.txt", "a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] {status} - {number} {details}\n")


# ---------- MAIN FUNCTION ----------
def send_whatsapp_messages(contacts, message, image_path=None, delay=2, log_callback=None):
    """
    Send WhatsApp messages with optional image attachment and caption.
    Optimized for instant caption → send click.
    """

    def log(text):
        print(text)
        if log_callback:
            log_callback(text + "\n")

    # ---------- CHROME SETUP ----------
    log("🧩 Initializing Chrome...")

    options = Options()
    options.add_experimental_option("detach", True)

    # Persistent user profile to avoid QR scan each time
    profile_path = os.path.join(os.getcwd(), "chrome_whatsapp_profile")
    os.makedirs(profile_path, exist_ok=True)
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        log(f"❌ Chrome launch failed: {e}")
        return

    # ---------- OPEN WHATSAPP ----------
    log("🔗 Opening WhatsApp Web...")
    driver.get("https://web.whatsapp.com")

    try:
        # If QR is visible
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
        )
        log("📲 QR code detected — please scan it once.")
        WebDriverWait(driver, 300).until_not(
            EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
        )
        log("✅ QR scanned successfully!")
    except Exception:
        log("✅ WhatsApp Web already logged in (session restored).")

    # ---------- IMAGE SENDER ----------
    def send_image_with_caption(img_path, caption):
        """Attach an image and send instantly with caption."""
        try:
            log("📎 Attaching image...")

            # 1️⃣ Click the attach button
            attach_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@aria-label='Attach' or @title='Attach']")
                )
            )
            driver.execute_script("arguments[0].click();", attach_btn)
            time.sleep(0.7)

            # 2️⃣ Select and upload image
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//input[@accept='image/*,video/mp4,video/3gpp,video/quicktime']",
                    )
                )
            )
            file_input.send_keys(img_path)
            log("🖼️ Image selected, waiting for preview...")
            time.sleep(2.0)

            # 3️⃣ Wait for preview or send button to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@aria-label='Send' or @role='button']")
                )
            )

            # 4️⃣ Type caption (fast paste)
            caption_added = False
            caption_selectors = [
                "//div[@contenteditable='true'][@data-tab='10']",
                "//div[@role='textbox'][@contenteditable='true']",
                "//div[contains(@aria-label,'Type a message')]",
            ]
            for sel in caption_selectors:
                try:
                    caption_box = driver.find_element(By.XPATH, sel)
                    driver.execute_script(
                        "arguments[0].scrollIntoView(true);", caption_box
                    )
                    caption_box.click()
                    pyperclip.copy(caption)
                    caption_box.send_keys(Keys.CONTROL, "v")
                    caption_added = True
                    log("✅ Caption added successfully.")
                    break
                except Exception:
                    continue

            if not caption_added:
                log("⚠️ Could not add caption, sending image only.")

            # 5️⃣ Instantly find and click send button (no extra wait)
            send_btn_selectors = [
                "//span[@data-icon='send']/ancestor::button",
                "//button[@aria-label='Send' or @title='Send']",
                "//div[@aria-label='Send']",
            ]

            send_btn = None
            # ⚡ Try finding immediately
            for sel in send_btn_selectors:
                try:
                    send_btn = driver.find_element(By.XPATH, sel)
                    if send_btn.is_enabled():
                        break
                except Exception:
                    continue

            # fallback: short wait if not found instantly
            if not send_btn:
                send_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[@aria-label='Send' or @title='Send']")
                    )
                )

            # 🚀 Hit send immediately (no delay)
            driver.execute_script("arguments[0].click();", send_btn)
            log("✅ Image (and caption) sent instantly.")
            return True

        except Exception as e:
            log(f"⚠️ Image send failed: {e}")
            return False

    # ---------- MAIN LOOP ----------
    for idx, number in enumerate(contacts, start=1):
        try:
            log(f"\n📤 Sending to {number} ({idx}/{len(contacts)})...")
            driver.get(f"https://web.whatsapp.com/send?phone={number}&text=")
            time.sleep(delay)

            # Wait for chat to load
            input_box = None
            for _ in range(20):
                try:
                    input_box = driver.find_element(
                        By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'
                    )
                    break
                except NoSuchElementException:
                    time.sleep(0.3)

            if not input_box:
                log(f"⚠️ Chat box not found for {number}. Skipping.")
                log_result("❌ FAILED", number, "(Chat box not found)")
                continue

            # --- Send Image First ---
            if image_path and os.path.exists(image_path):
                success = send_image_with_caption(image_path, message)
                if not success:
                    log("⚠️ Image failed, sending text only.")
                    pyperclip.copy(message)
                    input_box.click()
                    input_box.send_keys(Keys.CONTROL, "v")
                    input_box.send_keys(Keys.ENTER)
                    log("✅ Text sent as fallback.")
                    log_result("✅ TEXT ONLY SENT", number)
                else:
                    log_result("✅ IMAGE+TEXT SENT", number)
            else:
                # Text only
                pyperclip.copy(message)
                input_box.click()
                input_box.send_keys(Keys.CONTROL, "v")
                input_box.send_keys(Keys.ENTER)
                log("✅ Text message sent.")
                log_result("✅ TEXT SENT", number)

            time.sleep(delay)

        except WebDriverException as e:
            log(f"⚠️ Failed to send to {number}: {e}")
            log_result("❌ FAILED", number, str(e))

    log("\n🎉 All messages processed successfully!")
    log("📝 Chrome will stay open — close it manually when done.")
    # Note: We no longer auto-close Chrome
    # driver.quit()


# ---------- TEST RUN ----------
if __name__ == "__main__":
    test_contacts = ["91XXXXXXXXXX"]  # Replace with your test number
    test_message = "🚀 Instant caption test (send button speed optimized)"
    test_image = os.path.join(os.getcwd(), "media", "test.jpg")  # adjust if needed

    send_whatsapp_messages(test_contacts, test_message, image_path=test_image, delay=1.5)
