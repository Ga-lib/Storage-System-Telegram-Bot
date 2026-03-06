## Storage System with Telegram Bot [Manage file storage across Google Drive and Dropbox]

🤖 Hybrid Multi-Cloud Storage System with Telegram Bot
A sophisticated storage management solution that aggregates multiple Google Drive and Dropbox accounts into a single "Smart Storage" pool. Users can interact with their cloud storage via a Telegram Bot for mobile access or a CLI (Command Line Interface) for advanced management.

🚀 Key Features
🔹 Unified Storage Management
Account Aggregation: Combines multiple Google Drive and Dropbox accounts to bypass individual storage limits.

Smart Upload: Automatically calculates the remaining space across all accounts and selects the optimal service for your file.

Chunked Uploading: If a file is too large for any single account, the system automatically splits the file into chunks, distributes them across accounts, and reassembles them upon download.


🔹 Dual-Interface Access
Telegram Bot (bot.py): * /register: Link your Telegram ID to specific cloud accounts.

/storages: View real-time storage statistics (Used vs. Total).

/list: View all files across all linked cloud providers.

/upload: Send any document or photo to the bot to store it in the cloud.

/download: Retrieve files from the cloud directly into your Telegram chat.

Smart CLI (main.py): A terminal-based dashboard for bulk file management and system monitoring.


🔹 Security & Automation
OAuth 2.0 Integration: Secure authentication for Google Drive using client secrets and token rotation.

Session Persistence: Uses a local database (user_db.py) to remember user preferences and linked accounts.



🛠️ Technical Architecture
The "Smart" Logic
The system uses a Greedy Algorithm for file placement:

Check Capacity: Scans all linked accounts for available space.

Optimal Selection: Sorts services by remaining space and picks the smallest account that can still fit the entire file.

Automatic Fallback: If no single account is large enough, it triggers the Chunking Utility to split the file.



🔧 Installation & Setup
1. Clone the Repo: git clone https://github.com/Ga-lib/Storage-System-Telegram-Bot.git
cd Storage-System-Telegram-Bot

2. Install Dependencies: pip install python-telegram-bot google-auth-oauthlib google-api-python-client dropbox httpx
3. Configure API Keys:
Telegram: Replace your bot token here in bot.py with your token from @BotFather.
Google Drive: Place your client_secrets.json in the credentials/ folder.
Dropbox: Generate an Access Token from the Dropbox Developer Console and add it to the accounts dictionary.
4. Run the Bot: python bot.py

🔹Results:

<img width="485" height="873" alt="image" src="https://github.com/user-attachments/assets/c0dc067b-5d4c-4773-9c26-2dfae67b9a62" />
🔹🔹🔹🔹🔹🔹🔹🔹🔹
<img width="480" height="842" alt="image" src="https://github.com/user-attachments/assets/fc5966e4-36e5-4105-a0e0-fbf994920ffa" />
🔹🔹🔹🔹🔹🔹🔹🔹🔹
<img width="483" height="797" alt="image" src="https://github.com/user-attachments/assets/b770953f-d5e2-4ae2-be1f-faf035a8218a" />
🔹🔹🔹🔹🔹🔹🔹🔹🔹
<img width="480" height="858" alt="image" src="https://github.com/user-attachments/assets/131b9f47-8ba6-4e11-951e-50401769d77b" />
🔹🔹🔹🔹🔹🔹🔹🔹🔹
<img width="482" height="592" alt="image" src="https://github.com/user-attachments/assets/7192dd77-5317-46e9-b2f8-130b288deb5f" />
🔹🔹🔹🔹🔹🔹🔹🔹🔹
<img width="479" height="857" alt="image" src="https://github.com/user-attachments/assets/5aad35a6-de14-4336-99c2-d467d0b91248" />
🔹🔹🔹🔹🔹🔹🔹🔹🔹
<img width="479" height="858" alt="image" src="https://github.com/user-attachments/assets/735f22ba-f477-420d-b086-950919ebf1ff" />







