import zipfile

PROXY_HOST = "194.67.219.203"  # IP прокси
PROXY_PORT = "9315"  # Порт прокси
PROXY_USER = "APFRcJ"  # Логин прокси
PROXY_PASS = "sajzvS"  # Пароль прокси

manifest_json = """{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Proxy Authentication Plugin",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}"""

background_js = f"""
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{PROXY_HOST}",
            port: parseInt({PROXY_PORT})
        }},
        bypassList: []
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

chrome.webRequest.onAuthRequired.addListener(
    function(details) {{
        return {{
            authCredentials: {{
                username: "{PROXY_USER}",
                password: "{PROXY_PASS}"
            }}
        }};
    }},
    {{urls: ["<all_urls>"]}},
    ["blocking"]
);
"""

plugin_file = "proxy_auth_plugin.zip"
with zipfile.ZipFile(plugin_file, 'w') as zp:
    zp.writestr("manifest.json", manifest_json)
    zp.writestr("background.js", background_js)

print(f"Создано расширение {plugin_file}")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_extension("proxy_auth_plugin.zip")  # Подключаем прокси-расширение

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://kad.arbitr.ru")  # Проверяем IP

input("Нажмите Enter для закрытия...")
driver.quit()
