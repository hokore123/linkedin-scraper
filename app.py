from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)
SECRET_TOKEN = "abc123456"  # Make sure this matches your n8n Bearer Auth token

@app.route('/scrape', methods=['POST'])
def scrape_profiles():
    # 📥 DEBUG: Show all incoming headers
    print("📥 HEADERS RECEIVED:", dict(request.headers))

    # 🔒 Authorization check
    token = request.headers.get("Authorization")
    if token != f"Bearer {SECRET_TOKEN}":
        print("❌ Unauthorized - token mismatch:", token)
        return jsonify({"error": "Unauthorized"}), 401

    # 📦 Get and validate JSON body
    data = request.get_json()
    print("📦 BODY RECEIVED:", data)

    if not data or 'urls' not in data:
        return jsonify({'error': 'Missing LinkedIn URLs'}), 400

    urls = data['urls']
    if not isinstance(urls, list):
        return jsonify({'error': 'URLs must be a list'}), 400

    # ⚙️ Setup Selenium
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    results = []

    try:
        # 🧠 Login cookie injection
        driver.get("https://www.linkedin.com")
        driver.add_cookie({
            'name': 'li_at',
            'value': 'AQEDAQSkLpQCbHrqAAABlpbZzngAAAGXDHbOJVYABMlnqcPC_dAlA6rWV0yh4Kt1szOHC8bC1xNtvpUCCY7E9vr6pG1oyUbsbznhGBokuVR6y7iuR1xrEMeOJut9Y8Y9iv0_h3eFS-cKE4eX5TH7N7Ys',  # Replace with your actual LinkedIn session token
            'domain': '.linkedin.com'
        })
        driver.get("https://www.linkedin.com")  # Reload to apply cookie

        # 🔍 Loop through profiles
        for profile_url in urls:
            try:
                driver.get(profile_url)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                headline_elem = soup.select_one('div.text-body-medium.break-words')
                headline = headline_elem.get_text(strip=True) if headline_elem else 'Not found'

                results.append({
                    'url': profile_url,
                    'headline': headline
                })

            except Exception as e:
                results.append({
                    'url': profile_url,
                    'error': str(e)
                })

    finally:
        driver.quit()

    return jsonify(results)
