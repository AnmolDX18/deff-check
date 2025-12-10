🔍 Web Page Change Detector (Streamlit App)

A powerful web monitoring tool built with Streamlit that allows you to track, compare, and visualize changes in any public webpage over time. It detects updates at the HTML, text content, and visual rendering levels with advanced side-by-side and highlighted comparisons.

🚀 Features

✅ Save historical versions of any webpage
✅ Detect HTML source code changes
✅ Detect visible text content changes
✅ Side-by-side visual rendering of old vs new page
✅ Live highlighted visual changes:

🔴 Red = Removed

🟢 Green = Added
✅ Change percentage metrics
✅ Version history tracking per URL
✅ Download old and new text versions
✅ Clean and responsive Streamlit UI

🛠️ Tech Stack

Python

Streamlit

Requests

BeautifulSoup

Difflib

Pillow

HTML / CSS Rendering

📁 Project Structure
.
├── sapp.py                # Main Streamlit application
├── saved_pages/           # Auto-generated folder for saved HTML versions
└── README.md              # Project documentation

⚙️ Installation
1️⃣ Clone the repository
git clone <your-repo-url>
cd web-page-change-detector

2️⃣ Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

3️⃣ Install dependencies
pip install -r requirements.txt


If you don’t have requirements.txt, install manually:

pip install streamlit requests beautifulsoup4 pillow

▶️ How to Run the App
streamlit run sapp.py


The app will open in your browser automatically.

🧭 How to Use
✅ Step 1: Enter URL

Paste any public webpage URL into the input box.

✅ Step 2: Save Current Version

Click 📥 Save Current to store the page snapshot.

✅ Step 3: Detect Changes

Click 🔄 Check Changes to compare:

Latest version

Previously saved version

📊 Output Views Explained
Tab	Description
📝 Code Diff	Raw HTML line-by-line changes
👁️ Visual Comparison	Clean side-by-side page rendering
🔴 Highlighted Visual	Live red & green change highlights
📄 Text Changes	Structured text diff viewer
📈 Change Detection Logic

HTML Similarity → Measures structural changes

Text Similarity → Measures real visible content changes

Status Indicator

🟢 No Change → < 1%

🟡 Minor Change → 1–5%

🔴 Significant Change → > 5%

📂 Version Storage System

Each saved page is stored as:

saved_pages/<url_hash>_<timestamp>.html


The app supports multiple historical versions per URL

💡 Use Cases

✅ Monitor news article updates

✅ Track price changes

✅ Detect policy or documentation modifications

✅ Watch SEO content updates

✅ Audit unauthorized site changes

⚠️ Limitations

Some websites block iframe rendering

Heavy JavaScript sites may show partial diffs

Highlighting accuracy depends on text availability in the DOM

🧪 Future Enhancements (Optional)

Screenshot-based visual diff

Email alerts on change detection

Database-based version storage

Multi-URL bulk monitoring

Advanced XPath-based highlighting

🏁 Version

v2.0 – Visual Change Detection with Highlighting

📜 License

This project is open for personal and internal commercial use. Modify as needed.
