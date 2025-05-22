import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Function to clean text
def clean(text):
    return "".join(c if c.isalnum() else "_" for c in text)

# Function to scrape emails
def scrape_emails(username=None, password=None, folder="INBOX"):
    try:
        # Use environment variables if username or password is not provided
        username = username or os.getenv("GMAIL_USERNAME")
        password = password or os.getenv("GMAIL_PASSWORD")

        if not username or not password:
            raise ValueError("Gmail credentials are not provided or set in environment variables.")

        # Connect to the server
        imap = imaplib.IMAP4_SSL("imap.gmail.com")

        # Login to the account
        imap.login(username, password)

        # Select the mailbox you want to use
        imap.select(folder)

        # Search for all emails
        status, messages = imap.search(None, "ALL")

        # Convert messages to a list of email IDs
        messages = messages[0].split()

        for mail in messages:
            # Fetch the email by ID
            res, msg = imap.fetch(mail, "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    # Parse a bytes email into a message object
                    msg = email.message_from_bytes(response[1])

                    # Decode the email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        # If it's a bytes, decode to str
                        subject = subject.decode(encoding if encoding else "utf-8")
                    print("Subject:", subject)

                    # Decode email sender
                    from_ = msg.get("From")
                    print("From:", from_)

                    # If the email message is multipart
                    if msg.is_multipart():
                        # Iterate over email parts
                        for part in msg.walk():
                            # Extract content type of email
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            try:
                                # Get the email body
                                body = part.get_payload(decode=True).decode()
                                print("Body:", body)
                            except:
                                pass
                    else:
                        # Extract content type of email
                        content_type = msg.get_content_type()
                        # Get the email body
                        body = msg.get_payload(decode=True).decode()
                        print("Body:", body)

        # Close the connection and logout
        imap.close()
        imap.logout()

    except Exception as e:
        print("An error occurred:", e)

# Function to scrape the latest 5 emails
def scrape_latest_emails(username=None, password=None, folder="INBOX", count=5, blocklist=None):
    try:
        # Use environment variables if username or password is not provided
        username = username or os.getenv("GMAIL_USERNAME")
        password = password or os.getenv("GMAIL_PASSWORD")

        if not username or not password:
            raise ValueError("Gmail credentials are not provided or set in environment variables.")

        # Connect to the server
        imap = imaplib.IMAP4_SSL("imap.gmail.com")

        # Login to the account
        imap.login(username, password)

        # Select the mailbox you want to use
        imap.select(folder)

        # Search for all emails
        status, messages = imap.search(None, "ALL")

        # Convert messages to a list of email IDs
        messages = messages[0].split()

        # Get the latest 'count' emails
        latest_emails = messages[-count:]

        email_data = {}

        # Default blocklist if none provided
        if blocklist is None:
            blocklist = []

        for mail in reversed(latest_emails):
            # Fetch the email by ID
            res, msg = imap.fetch(mail, "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    # Parse a bytes email into a message object
                    msg = email.message_from_bytes(response[1])

                    # Decode the email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        # If it's a bytes, decode to str
                        subject = subject.decode(encoding if encoding else "utf-8")

                    # Decode email sender
                    from_ = msg.get("From")

                    # Decode the email date
                    date = msg.get("Date")

                    # If the email message is multipart
                    body = ""
                    if msg.is_multipart():
                        # Iterate over email parts
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            try:
                                body = part.get_payload(decode=True).decode()
                                break
                            except:
                                pass
                    else:
                        body = msg.get_payload(decode=True).decode()

                    # Check if the email should be blocked
                    if any(keyword in (subject or "") for keyword in blocklist) or any(keyword in (from_ or "") for keyword in blocklist):
                        continue

                    # Store the email data in the dictionary
                    email_data[mail.decode()] = {
                        "subject": subject,
                        "from": from_,
                        "body": body,
                        "date": date
                    }

        # Close the connection and logout
        imap.close()
        imap.logout()

        return email_data

    except Exception as e:
        print("An error occurred:", e)
        return {}

if __name__ == "__main__":
    blocklist = ["no-reply@accounts.google.com", "Security alert","unstop","linkedin", "kaggle", "Team Unstop", "Canva", "noreply@github.com", "noreply", "feed"]
    print("Fetching the latest 1000 emails...")
    emails = scrape_latest_emails(count=1000, blocklist=blocklist)
    print(emails)