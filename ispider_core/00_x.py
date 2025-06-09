from seleniumbase import Driver
import time
import os

def scrape_x_profile(url, scrolls=100, save_interval=10, delay=2):
    driver = Driver(uc=True)  # Undetectable Chrome
    driver.get(url)
    time.sleep(5)  # Initial load

    os.makedirs("html_dumps", exist_ok=True)

    for i in range(1, scrolls + 1):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)

        if i % save_interval == 0:
            html = driver.page_source
            filename = f"html_dumps/page_{i}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"[+] Saved {filename}")

    driver.quit()

if __name__ == "__main__":
    scrape_x_profile("https://x.com/HeyAmit_", scrolls=100, save_interval=10, delay=2)
