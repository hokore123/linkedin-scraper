from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import tempfile
import shutil

app = Flask(__name__)

# 🔐 Set token from env or fallback to hardcoded one (dev/testing)
SECRET_TOKEN = os.environ.get("SECRET_TOKEN", "secureToken_123ABC456def789XYZ")
LI_AT_COOKIE = os.environ.get("LI_AT_COOKIE", "AQEDAQSkLpQCbHrqAAABlpbZzngAAAGXDHbOJVYABMlnqcPC_dAlA6rWV0yh4Kt1szOHC8bC1xNtvpUCCY7E9vr6pG1oyUbsbznhGBokuVR6y7iuR1xrEMeOJut9Y8Y9iv0_h3eFS-cKE4eX5TH7N7Ys")

@app.route('/scrape', methods=['POST'])
def scrape_profiles():
    # 🛡️ Check Authorization
    token = request.headers.get("Authorization")
    if token != f"Bearer {SECRET_TOKEN}":
        print("❌ Invalid token:", token)
        return jsonify({"error": "Unauthorized"}), 401

    # 📦 Parse JSON input
    data = request.get_json()
    print("📨 Incoming body:", data)

    if not data or 'urls' not in data:
        return jsonify({'error': 'Missing LinkedIn URLs'}), 400

    urls = data['urls']
    if not isinstance(urls, list):
        return jsonify({'error': 'URLs must be a list'}), 400

    # ⚙️ Setup Selenium (headless Chrome)
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Create a unique user data directory
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f'--user-data-dir={user_data_dir}')

    driver = webdriver.Chrome(options=options)
    results = []

    try:
        driver.get("https://www.linkedin.com")
        driver.add_cookie({
            'name': 'li_at',
            'value': LI_AT_COOKIE,
            'domain': '.linkedin.com'
        })
        driver.get("https://www.linkedin.com")  # Reload with cookie

        for profile_url in urls:
            if not profile_url.startswith("http"):
                results.append({"url": profile_url, "error": "Invalid URL"})
                continue

            try:
                print("🔍 Scraping:", profile_url)
                driver.get(profile_url)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                headline_elem = soup.select_one('div.text-body-medium.break-words')
                headline = headline_elem.get_text(strip=True) if headline_elem else 'Not found'

                results.append({
                    'url': profile_url,
                    'headline': headline
                })

            except Exception as e:
                results.append({'url': profile_url, 'error': str(e)})

    finally:
        driver.quit()
        # Remove the temporary directory
        if os.path.exists(user_data_dir):
            shutil.rmtree(user_data_dir)

    return jsonify(results)
