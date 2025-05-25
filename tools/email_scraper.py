import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Function to clean text
def clean(text):
    return "".join(c if c.isalnum() else "_" for c in text)

class EmailScraper:
    def __init__(self, username=None, password=None):
        """
        Initialize the EmailScraper with optional username and password.
        If not provided, credentials are fetched from environment variables.
        """
        self.username = username or os.getenv("GMAIL_USERNAME")
        self.password = password or os.getenv("GMAIL_PASSWORD")

        if not self.username or not self.password:
            raise ValueError("Gmail credentials are not provided or set in environment variables.")

    def _connect(self):
        """Connect to the Gmail IMAP server and login."""
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(self.username, self.password)
        return imap

    def scrape_emails(self, folder="INBOX"):
        """Scrape all emails from the specified folder."""
        try:
            imap = self._connect()
            imap.select(folder)

            status, messages = imap.search(None, "ALL")
            messages = messages[0].split()

            for mail in messages:
                res, msg = imap.fetch(mail, "(RFC822)")
                for response in msg:
                    if isinstance(response, tuple):
                        msg = email.message_from_bytes(response[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        print("Subject:", subject)

                        from_ = msg.get("From")
                        print("From:", from_)

                        if msg.is_multipart():
                            for part in msg.walk():
                                try:
                                    body = part.get_payload(decode=True).decode()
                                    print("Body:", body)
                                except:
                                    pass
                        else:
                            body = msg.get_payload(decode=True).decode()
                            print("Body:", body)

            imap.close()
            imap.logout()

        except Exception as e:
            print("An error occurred:", e)

    def scrape_latest_emails(self, folder="INBOX", count=5, blocklist=None):
        """Scrape the latest emails with optional blocklist filtering."""
        try:
            imap = self._connect()
            imap.select(folder)

            status, messages = imap.search(None, "ALL")
            messages = messages[0].split()
            latest_emails = messages[-count:]

            email_data = {}
            blocklist = blocklist or []

            for mail in reversed(latest_emails):
                try:
                    res, msg = imap.fetch(mail, "(RFC822)")
                    for response in msg:
                        if isinstance(response, tuple):
                            msg = email.message_from_bytes(response[1])
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else "utf-8")

                            from_ = msg.get("From")
                            date = msg.get("Date")

                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    try:
                                        body = part.get_payload(decode=True).decode()
                                        break
                                    except:
                                        pass
                            else:
                                body = msg.get_payload(decode=True).decode()

                            if any(keyword in (subject or "") for keyword in blocklist) or \
                               any(keyword in (from_ or "") for keyword in blocklist):
                                logging.info(f"Blocked email from: {from_}, subject: {subject}")
                                continue

                            email_data[mail.decode()] = {
                                "subject": subject,
                                "from": from_, 
                                "body": body,
                                "date": date,
                                "metadata": {
                                    "subject": subject,
                                    "from": from_,
                                    "date": date
                                }
                            }
                except Exception as e:
                    logging.error(f"Error processing email ID {mail.decode()}: {e}")

            imap.close()
            imap.logout()

            return email_data

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return {}

if __name__ == "__main__":
    import json

    blocklist = ["no-reply@accounts.google.com", "Security alert", "unstop", "linkedin", "kaggle", "Team Unstop", "Canva", "noreply@github.com", "noreply", "feed"]
    logging.info("Fetching the latest 10,000 emails...")

    scraper = EmailScraper()
    emails = scraper.scrape_latest_emails(count=10000, blocklist=blocklist)

    # Save the emails to a JSON file
    output_file = "latest_emails.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(emails, f, ensure_ascii=False, indent=4)

    logging.info(f"Fetched emails saved to {output_file}")