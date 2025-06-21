import pygetwindow as gw
import pyautogui
import time
import cv2
import numpy as np

# === CONFIGURATION ===
WINDOW_TITLE = "Etheria:Restart"  # Replace with the actual title
THRESHOLD = 0.8                          # Confidence threshold for matching
CHECK_INTERVAL = 10                      # Seconds between checks

# === Load reference images ===
complete_img = cv2.imread("assets/complete.png")
challenge_img = cv2.imread("assets/challenge.png")
play_again_img = cv2.imread("assets/play-again.png")
battle_img = cv2.imread("assets/battle.png")
post_battle_img = cv2.imread("assets/post-battle.png")

def get_window_rect(title):
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        print(f"[ERROR] No window found with title: {title}")
        return None
    win = windows[0]
    if not win.isActive:
        win.activate()
        time.sleep(0.5)
    return (win.left, win.top, win.width, win.height)

def screenshot_window(title):
    rect = get_window_rect(title)
    if rect:
        x, y, w, h = rect
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        return screenshot, (x, y)
    return None, (0, 0)

def locate_and_click(template_img, description, window_offset):
    screenshot, offset = screenshot_window(WINDOW_TITLE)
    if screenshot is None:
        return False
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    result = cv2.matchTemplate(screenshot_bgr, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= THRESHOLD:
        h, w = template_img.shape[:2]
        click_x = offset[0] + max_loc[0] + w // 2
        click_y = offset[1] + max_loc[1] + h // 2
        print(f"[INFO] Clicking {description} at ({click_x}, {click_y})")
        pyautogui.click(click_x, click_y)
        return True
    else:
        print(f"[INFO] {description} not found (confidence={max_val:.2f})")
        return False

# === Main Loop ===
def main():
    print("[INFO] Autoclicker started. Press Ctrl+C to stop.")
    try:
        while True:
            print("[INFO] Checking for 'Complete' button...")
            found = locate_and_click(complete_img, "Complete", get_window_rect(WINDOW_TITLE))
            # If found, click "play-again" and then click the "challenge" button
            if found:
                locate_and_click(play_again_img, "Play Again", get_window_rect(WINDOW_TITLE))
            else:
                print("[INFO] 'Complete' not found. Trying 'Challenge'...")
                if locate_and_click(challenge_img, "Challenge", get_window_rect(WINDOW_TITLE)):
                    time.sleep(2)  # Wait for next UI screen to load
                    locate_and_click(battle_img, "Battle", get_window_rect(WINDOW_TITLE))

                    # Wait for the post-battle screen to appear before clicking
                    print("[INFO] Waiting for post-battle screen...")
                    while not locate_and_click(post_battle_img, "Post Battle", get_window_rect(WINDOW_TITLE)):
                        time.sleep(3)  # Check every second for the post-battle screen

            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n[INFO] Script stopped by user.")

if __name__ == "__main__":
    main()