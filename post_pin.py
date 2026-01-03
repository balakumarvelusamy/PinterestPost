import json
import time
import shutil
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent
TO_POST = BASE_DIR / "to_post"
POSTED = BASE_DIR / "posted"
#create above 2 folders if they don't exist
TO_POST.mkdir(exist_ok=True)
POSTED.mkdir(exist_ok=True)
SESSION_FILE = BASE_DIR / "pinterest_session.json"

with open(BASE_DIR / "config.json") as f:
    config = json.load(f)

def get_next_image():
    # Glob for both jpg and png, sort to be deterministic
    images = sorted(list(TO_POST.glob("*.jpg")) + list(TO_POST.glob("*.png")))
    return images[0] if images else None

def main():
    image = get_next_image()
    if not image:
        print("No images to post.")
        return

    print(f"Processing image: {image.name}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Load storage state if exists
        state_path = SESSION_FILE if SESSION_FILE.exists() else None
        context = browser.new_context(storage_state=state_path)
        page = context.new_page()

        # Check login or force login
        if not SESSION_FILE.exists():
            print("➡️ Session not found. Please login manually in the browser window.")
            page.goto("https://www.pinterest.com/login/")
            print("➡️ Login manually, then press ENTER here to save session and continue...")
            input()
            context.storage_state(path=SESSION_FILE)
            print("✅ Session saved.")
        else:
            print("Using existing session.")

        # Go to Pin Builder
        page.goto("https://www.pinterest.com/pin-creation-tool/")
        time.sleep(5)

        # Basic check if we are redirected to login (session expired)
        if "login" in page.url:
             print("➡️ Session expired. Please login manually, then press ENTER here...")
             input()
             context.storage_state(path=SESSION_FILE)
             # Retry going to builder
             page.goto("https://www.pinterest.com/pin-creation-tool/")
             time.sleep(5)

        try:
            # Upload image
            page.set_input_files('input[type="file"]', str(image))
            time.sleep(3)

            # Fill Title
            page.get_by_placeholder("Add a title").fill(config["title"])
            # Fill Description (Rich Text Editor)
            # Use exact description from config
            desc_text = config["description"]
            # Click the editor content div. Use force=True as it sometimes appears disabled/unstable.
            page.locator('.public-DraftEditor-content').click(force=True)
            page.keyboard.type(desc_text)

            # Destination Link
            page.get_by_placeholder("Add a link").fill(config["link"])
            # Select Board
            # "Choose a board" is text, not a placeholder attribute. Use data-test-id.
            page.click('[data-test-id="board-dropdown-select-button"]')
            time.sleep(2)
            
            # Search for board in the dropdown
            # Use specific ID
            page.locator('#pickerSearchField').fill(config["board_name"])
            time.sleep(2)
            # Click the board with the matching title
            page.click(f'div[title="{config["board_name"]}"]')
            time.sleep(2)

            # Additional Tags (Tagged Topics field)
            # This handles the specific "Tagged topics" input
            tag_input = page.get_by_placeholder("Search for a tag")
            for tag in config["tags"]:
                tag_input.fill(tag)
                time.sleep(2) # Wait for suggestions
                page.keyboard.press("Enter") # Select first suggestion
                time.sleep(1)

          


            # Click Publish
            page.click('button:has-text("Publish")')
            print("Publishing...")
            time.sleep(10) # Wait for publish to complete
            shutil.move(str(image), POSTED / image.name)
            print(f"✅ Posted and moved: {image.name}")

        except Exception as e:
            print(f"❌ Error occurred: {e}")
            # Capture screenshot
            page.screenshot(path="error.png")

        browser.close()

if __name__ == "__main__":
    main()
