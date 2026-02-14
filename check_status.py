import os
import requests
import cloudscraper
from bs4 import BeautifulSoup

URL = "https://support.italki.com/hc/en-us/articles/115001499873-Is-my-language-open-for-application"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STATE_FILE = "last_status.txt"

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def get_russian_status():
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the table. italki uses a standard table structure.
        table = soup.find("table")
        if not table:
            return None, None

        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 3:
                language = cells[0].get_text(strip=True)
                if "Russian" in language:
                    # Professional Teacher is usually the 2nd column, Community Tutor the 3rd
                    prof_status = cells[1].get_text(strip=True)
                    comm_status = cells[2].get_text(strip=True)
                    return prof_status, comm_status
    except Exception as e:
        print(f"Error fetching status: {e}")
    return None, None

def main():
    prof, comm = get_russian_status()
    
    if prof is None or comm is None:
        print("Could not find Russian status in the table.")
        return

    current_status = f"Prof: {prof}, Comm: {comm}"
    print(f"Current Status: {current_status}")

    # Load previous status
    last_status = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            last_status = f.read().strip()

    # Logic: Notify if status is "Closed" (TESTING MODE)
    is_open = "Closed" in prof or "Closed" in comm
    
    if is_open and current_status != last_status:
        message = (
            f"🚨 *italki Russian Application Status Change!* 🚨\n\n"
            f"• Professional Teacher: *{prof}*\n"
            f"• Community Tutor: *{comm}*\n\n"
            f"[Check here]({URL})"
        )
        send_telegram_message(message)
        print("Notification sent!")
    
    # Update the state file
    with open(STATE_FILE, "w") as f:
        f.write(current_status)

if __name__ == "__main__":
    main()
