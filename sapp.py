import streamlit as st
import requests
from bs4 import BeautifulSoup
import difflib
from datetime import datetime
import hashlib
from pathlib import Path
import re
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# Initialize session state
if 'saved_pages' not in st.session_state:
    st.session_state.saved_pages = {}
if 'comparison_result' not in st.session_state:
    st.session_state.comparison_result = None

# Create directory for saved pages
SAVE_DIR = Path("saved_pages")
SAVE_DIR.mkdir(exist_ok=True)

def fetch_page(url):
    """Fetch webpage content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        st.error(f"Error fetching page: {str(e)}")
        return None

def save_page(url, content):
    """Save page content to disk"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename = f"{url_hash}_{timestamp}.html"
    filepath = SAVE_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Save metadata
    metadata = {
        'url': url,
        'timestamp': timestamp,
        'filepath': str(filepath),
        'display_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if url not in st.session_state.saved_pages:
        st.session_state.saved_pages[url] = []
    st.session_state.saved_pages[url].append(metadata)
    
    return filepath

def get_text_diff(old_content, new_content):
    """Generate line-by-line diff"""
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    
    diff = difflib.unified_diff(old_lines, new_lines, lineterm='', n=3)
    diff_list = list(diff)
    
    # Limit to first 500 lines to avoid overwhelming display
    if len(diff_list) > 500:
        diff_list = diff_list[:500] + ['... (truncated, showing first 500 lines)']
    
    return '\n'.join(diff_list)

def extract_text_content(html):
    """Extract visible text content from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "meta", "link"]):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    return '\n'.join(lines)

def create_text_comparison_html(old_text, new_text):
    """Create HTML showing text differences with highlighting"""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    
    html_parts = ["""
    <style>
        .comparison-container {
            display: flex;
            gap: 20px;
            font-family: monospace;
            font-size: 12px;
        }
        .version-panel {
            flex: 1;
            border: 1px solid #ddd;
            padding: 15px;
            background: white;
            overflow-y: auto;
            max-height: 600px;
        }
        .version-title {
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #333;
        }
        .line {
            padding: 2px 5px;
            margin: 1px 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .unchanged {
            background: white;
        }
        .changed {
            background: #ffcccc;
            border-left: 3px solid red;
            font-weight: bold;
        }
        .added {
            background: #ccffcc;
            border-left: 3px solid green;
        }
        .removed {
            background: #ffcccc;
            border-left: 3px solid red;
            text-decoration: line-through;
        }
    </style>
    <div class="comparison-container">
        <div class="version-panel">
            <div class="version-title">📁 Saved Version</div>
    """]
    
    old_output = []
    new_output = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_segment = old_lines[i1:i2]
        new_segment = new_lines[j1:j2]
        
        if tag == 'equal':
            for line in old_segment:
                old_output.append(f'<div class="line unchanged">{html_escape(line)}</div>')
            for line in new_segment:
                new_output.append(f'<div class="line unchanged">{html_escape(line)}</div>')
        elif tag == 'replace':
            for line in old_segment:
                old_output.append(f'<div class="line changed">{html_escape(line)}</div>')
            for line in new_segment:
                new_output.append(f'<div class="line changed">{html_escape(line)}</div>')
        elif tag == 'delete':
            for line in old_segment:
                old_output.append(f'<div class="line removed">{html_escape(line)}</div>')
        elif tag == 'insert':
            for line in new_segment:
                new_output.append(f'<div class="line added">{html_escape(line)}</div>')
    
    html_parts.append(''.join(old_output))
    html_parts.append("""
        </div>
        <div class="version-panel">
            <div class="version-title">🆕 Current Version</div>
    """)
    html_parts.append(''.join(new_output))
    html_parts.append("""
        </div>
    </div>
    """)
    
    return ''.join(html_parts)

def html_escape(text):
    """Escape HTML special characters"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))

def create_iframe_with_base(html_content, base_url):
    """Create an iframe with proper base URL set"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Add or update base tag
    base_tag = soup.find('base')
    if base_tag:
        base_tag['href'] = base_url
    else:
        if soup.head:
            base_tag = soup.new_tag('base', href=base_url)
            soup.head.insert(0, base_tag)
    
    # Add sandbox attribute notice
    notice = soup.new_tag('div', style='background:#ffffcc;padding:10px;border:2px solid #ff9900;margin:10px;')
    notice.string = '⚠️ Note: This is a rendered version. Some interactive features may not work. Images and styles are loaded from the original site.'
    
    if soup.body:
        soup.body.insert(0, notice)
    
    return str(soup)

def highlight_visual_changes(old_html, new_html, base_url, old_text_lines, new_text_lines):
    """Create side-by-side comparison with visual highlighting using text diff results"""
    # Create highlighted versions
    old_soup_highlighted = BeautifulSoup(old_html, 'html.parser')
    new_soup_highlighted = BeautifulSoup(new_html, 'html.parser')
    
    # Use the text comparison results to find what changed
    matcher = difflib.SequenceMatcher(None, old_text_lines, new_text_lines)
    
    removed_texts = set()
    added_texts = set()
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            # Text was changed
            for line in old_text_lines[i1:i2]:
                if line.strip() and len(line.strip()) > 3:
                    removed_texts.add(line.strip())
            for line in new_text_lines[j1:j2]:
                if line.strip() and len(line.strip()) > 3:
                    added_texts.add(line.strip())
        elif tag == 'delete':
            # Text was removed
            for line in old_text_lines[i1:i2]:
                if line.strip() and len(line.strip()) > 3:
                    removed_texts.add(line.strip())
        elif tag == 'insert':
            # Text was added
            for line in new_text_lines[j1:j2]:
                if line.strip() and len(line.strip()) > 3:
                    added_texts.add(line.strip())
    
    print(f"DEBUG: Removed texts ({len(removed_texts)}): {removed_texts}")
    print(f"DEBUG: Added texts ({len(added_texts)}): {added_texts}")
    
    # Add highlighting styles
    highlight_style_old = old_soup_highlighted.new_tag('style')
    highlight_style_old.string = """
        .change-highlight-removed {
            background-color: rgba(255, 0, 0, 0.25) !important;
            outline: 3px solid #ff0000 !important;
            outline-offset: 2px;
            box-shadow: 0 0 5px rgba(255, 0, 0, 0.5) !important;
        }
    """
    
    highlight_style_new = new_soup_highlighted.new_tag('style')
    highlight_style_new.string = """
        .change-highlight-added {
            background-color: rgba(0, 255, 0, 0.25) !important;
            outline: 3px solid #00ff00 !important;
            outline-offset: 2px;
            box-shadow: 0 0 5px rgba(0, 255, 0, 0.5) !important;
        }
    """
    
    if old_soup_highlighted.head:
        old_soup_highlighted.head.append(highlight_style_old)
    if new_soup_highlighted.head:
        new_soup_highlighted.head.append(highlight_style_new)
    
    # Function to find and highlight elements containing the text
    def highlight_elements(soup, texts_to_find, css_class, label):
        count = 0
        for text_target in texts_to_find:
            found = False
            # Search through all text elements
            for elem in soup.find_all(text=True):
                if elem.parent.name in ['script', 'style', 'meta', 'link', 'noscript']:
                    continue
                
                elem_text = elem.strip()
                
                # Try exact match first
                if elem_text == text_target:
                    parent = elem.parent
                    # Check if already highlighted
                    current_classes = parent.get('class', [])
                    if css_class in current_classes:
                        continue
                    
                    # Highlight the parent element
                    if current_classes:
                        parent['class'] = current_classes + [css_class]
                    else:
                        parent['class'] = [css_class]
                    count += 1
                    found = True
                    print(f"DEBUG {label}: Highlighted '{text_target[:50]}...' in <{parent.name}>")
                    break
                
                # Also try if the target is contained in this element's text
                elif text_target in elem_text and len(text_target) > 10:
                    parent = elem.parent
                    current_classes = parent.get('class', [])
                    if css_class in current_classes:
                        continue
                    
                    if current_classes:
                        parent['class'] = current_classes + [css_class]
                    else:
                        parent['class'] = [css_class]
                    count += 1
                    found = True
                    print(f"DEBUG {label}: Highlighted (partial) '{text_target[:50]}...' in <{parent.name}>")
                    break
            
            if not found:
                print(f"DEBUG {label}: Could not find element with text '{text_target[:50]}...'")
        
        return count
    
    # Apply highlights
    removed_count = highlight_elements(old_soup_highlighted, removed_texts, 'change-highlight-removed', 'OLD')
    added_count = highlight_elements(new_soup_highlighted, added_texts, 'change-highlight-added', 'NEW')
    
    print(f"DEBUG: Total highlighted - {removed_count} removed, {added_count} added")
    
    # Fix URLs
    for soup in [old_soup_highlighted, new_soup_highlighted]:
        for img in soup.find_all('img'):
            if img.get('src'):
                img['src'] = requests.compat.urljoin(base_url, img['src'])
        for link in soup.find_all('link'):
            if link.get('href'):
                link['href'] = requests.compat.urljoin(base_url, link['href'])
        for script in soup.find_all('script'):
            if script.get('src'):
                script['src'] = requests.compat.urljoin(base_url, script['src'])
    
    return str(old_soup_highlighted), str(new_soup_highlighted)

def compare_pages(old_content, new_content, url):
    """Compare two page versions"""
    # Code-level comparison (limited to avoid overwhelming output)
    code_diff = get_text_diff(old_content, new_content)
    
    # Calculate similarity
    similarity = difflib.SequenceMatcher(None, old_content, new_content).ratio()
    change_percentage = (1 - similarity) * 100
    
    # Extract and compare text content
    old_text = extract_text_content(old_content)
    new_text = extract_text_content(new_content)
    
    old_text_lines = old_text.splitlines()
    new_text_lines = new_text.splitlines()
    
    text_similarity = difflib.SequenceMatcher(None, old_text, new_text).ratio()
    visual_change_percentage = (1 - text_similarity) * 100
    
    # Create text comparison HTML
    text_comparison_html = create_text_comparison_html(old_text, new_text)
    
    # Create iframes with base URL (no highlighting)
    old_iframe = create_iframe_with_base(old_content, url)
    new_iframe = create_iframe_with_base(new_content, url)
    
    # Create highlighted visual comparison
    old_highlighted, new_highlighted = highlight_visual_changes(old_content, new_content, url, old_text_lines, new_text_lines)
    
    return {
        'code_diff': code_diff,
        'change_percentage': change_percentage,
        'visual_change_percentage': visual_change_percentage,
        'old_iframe': old_iframe,
        'new_iframe': new_iframe,
        'old_highlighted': old_highlighted,
        'new_highlighted': new_highlighted,
        'text_comparison_html': text_comparison_html,
        'old_text': old_text,
        'new_text': new_text
    }

# Streamlit UI
st.set_page_config(page_title="Web Page Change Detector", page_icon="🔍", layout="wide")

st.title("🔍 Web Page Change Detector")
st.markdown("Monitor and visualize changes in web pages")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    url = st.text_input("Enter URL to monitor:", placeholder="https://example.com", key="url_input")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Save Current", use_container_width=True):
            if url:
                with st.spinner("Fetching page..."):
                    content = fetch_page(url)
                    if content:
                        save_page(url, content)
                        st.success("✅ Page saved!")
                        st.rerun()
            else:
                st.warning("⚠️ Please enter a URL")
    
    with col2:
        if st.button("🔄 Check Changes", use_container_width=True):
            if url:
                if url in st.session_state.saved_pages and len(st.session_state.saved_pages[url]) > 0:
                    with st.spinner("Analyzing changes..."):
                        # Get current page
                        current_content = fetch_page(url)
                        if current_content:
                            # Get last saved version
                            last_saved = st.session_state.saved_pages[url][-1]
                            with open(last_saved['filepath'], 'r', encoding='utf-8') as f:
                                old_content = f.read()
                            
                            # Compare
                            st.session_state.comparison_result = compare_pages(old_content, current_content, url)
                            st.success("✅ Analysis complete!")
                            st.rerun()
                else:
                    st.warning("⚠️ No saved version found. Save the page first.")
            else:
                st.warning("⚠️ Please enter a URL")
    
    st.divider()
    
    # Show saved pages
    if url and url in st.session_state.saved_pages:
        st.subheader("📚 Saved Versions")
        for idx, page in enumerate(reversed(st.session_state.saved_pages[url])):
            with st.container():
                st.markdown(f"**Version {len(st.session_state.saved_pages[url]) - idx}**")
                st.caption(f"🕐 {page['display_time']}")
                if idx < len(st.session_state.saved_pages[url]) - 1:
                    st.markdown("---")

# Main content area
if st.session_state.comparison_result:
    result = st.session_state.comparison_result
    
    # Show change summary
    st.header("📊 Change Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Code Change", f"{result['change_percentage']:.2f}%", 
                 delta=f"{result['change_percentage']:.1f}%" if result['change_percentage'] > 0 else None)
    
    with col2:
        st.metric("Text Content Change", f"{result['visual_change_percentage']:.2f}%",
                 delta=f"{result['visual_change_percentage']:.1f}%" if result['visual_change_percentage'] > 0 else None)
    
    with col3:
        if result['visual_change_percentage'] > 5:
            status = "🔴 Significant"
            color = "red"
        elif result['visual_change_percentage'] > 1:
            status = "🟡 Minor"
            color = "orange"
        else:
            status = "🟢 No Changes"
            color = "green"
        st.markdown(f"**Status:** :{color}[{status}]")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Code Diff", "👁️ Visual Comparison", "🔴 Highlighted Visual", "📄 Text Changes"])
    
    with tab1:
        st.subheader("Code-Level Differences")
        st.info("💡 Shows raw HTML differences (first 500 lines)")
        if result['code_diff']:
            st.code(result['code_diff'], language='diff')
        else:
            st.success("✅ No code differences detected")
    
    with tab2:
        st.subheader("Side-by-Side Page Rendering (Clean)")
        st.warning("⚠️ Note: Some sites may not render perfectly due to security restrictions. Images and styles are loaded from the original URL.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📁 Saved Version**")
            st.components.v1.html(result['old_iframe'], height=700, scrolling=True)
        
        with col2:
            st.markdown("**🆕 Current Version**")
            st.components.v1.html(result['new_iframe'], height=700, scrolling=True)
    
    with tab3:
        st.subheader("🔴 Visual Comparison with Highlighted Changes")
        st.success("🎯 Red outline = Removed content | Green outline = Added content | Orange outline = Modified")
        st.info("💡 Changes are highlighted directly on the rendered pages below")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📁 Saved Version (Changes in Red)**")
            st.components.v1.html(result['old_highlighted'], height=700, scrolling=True)
        
        with col2:
            st.markdown("**🆕 Current Version (Changes in Green)**")
            st.components.v1.html(result['new_highlighted'], height=700, scrolling=True)
    
    with tab4:
        st.subheader("📄 Text Content Changes")
        st.info("🎯 Red = Changed/Removed | Green = Added | White = Unchanged")
        
        st.components.v1.html(result['text_comparison_html'], height=700, scrolling=True)
        
        # Download options
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Old Version Text",
                data=result['old_text'],
                file_name="old_version.txt",
                mime="text/plain"
            )
        with col2:
            st.download_button(
                label="📥 Download New Version Text",
                data=result['new_text'],
                file_name="new_version.txt",
                mime="text/plain"
            )

else:
    # Welcome screen
    st.info("👆 Enter a URL in the sidebar and click **'📥 Save Current'** to start monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 How to Use
        
        1. **Enter URL** - Paste any public website URL
        2. **Save Current** - Capture the current page state
        3. **Check Changes** - Compare current page with saved version
        4. **View Results** - Analyze differences in multiple views
        
        ### 📋 Best Practices
        
        - Save pages before expected changes
        - Check regularly for updates
        - Use for monitoring news, prices, or content
        - Download text versions for records
        """)
    
    with col2:
        st.markdown("""
        ### ✨ Features
        
        - **Code Diff** - Line-by-line HTML comparison
        - **Visual Rendering** - See pages side-by-side
        - **Text Highlighting** - Changes marked in red/green
        - **Change Metrics** - Percentage-based analysis
        - **Version History** - Track multiple snapshots
        - **Export Options** - Download text versions
        
        ### 💡 Use Cases
        
        - Monitor news article updates
        - Track price changes on e-commerce
        - Watch for policy/documentation updates
        - Detect website modifications
        """)

# Footer
st.divider()
st.caption("🔍 Web Page Change Detector v2.0 | Built with Streamlit | Detect • Compare • Visualize")
