import pygetwindow as gw
import time
import cv2
import numpy as np
import pyautogui
import os
import mss
import win32api
import win32con

# === CONFIGURATION ===
WINDOW_TITLE = "Etheria:Restart"
THRESHOLD = 0.8
CHECK_INTERVAL = 10

# === Utility: Load template images safely ===
def load_template(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[ERROR] File not found: {path}")
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"[ERROR] Failed to load image: {path}")
    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Convert from BGRA to BGR if needed
    return img

# === Load reference images from /assets ===
try:
    complete_img = load_template("assets/complete.png")
    challenge_img = load_template("assets/challenge.png")
    play_again_img = load_template("assets/play-again.png")
    battle_img = load_template("assets/battle.png")
    post_battle_img = load_template("assets/post-battle.png")
except Exception as e:
    print(e)
    exit(1)

def get_window_rect(title):
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        print(f"[ERROR] No window found with title: {title}")
        return None
    win = windows[0]
    screen_size = pyautogui.size()
    print(f"[DEBUG] Screen size: {screen_size}")
    print(f"[DEBUG] Window position: left={win.left}, top={win.top}, width={win.width}, height={win.height}")
    if not win.isActive:
        win.activate()
        time.sleep(0.5)
    return (win.left, win.top, win.width, win.height)

def screenshot_window(title):
    rect = get_window_rect(title)
    if rect:
        x, y, w, h = rect
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": w, "height": h}
            sct_img = sct.grab(monitor)
            img = np.array(sct_img)
            # MSS gives BGRA, convert to BGR
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img, (x, y)
    return None, (0, 0)

# Force click function
def force_click(x, y):
    win32api.SetCursorPos((x, y))
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def locate_and_click(template_img, description, window_offset):
    screenshot_bgr, offset = screenshot_window(WINDOW_TITLE)
    if screenshot_bgr is None:
        return False

    # Debug image saving
    os.makedirs("debug", exist_ok=True)
    cv2.imwrite(f"debug/debug_screenshot_{description}.png", screenshot_bgr)
    cv2.imwrite(f"debug/debug_template_{description}.png", template_img)

    result = cv2.matchTemplate(screenshot_bgr, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= THRESHOLD:
        h, w = template_img.shape[:2]
        click_x = offset[0] + max_loc[0] + w // 2
        click_y = offset[1] + max_loc[1] + h // 2

		# 🧠 Reactivate game window
        win = gw.getWindowsWithTitle(WINDOW_TITLE)[0]
        if not win.isActive:
            win.activate()
            time.sleep(0.2)

        print(f"[INFO] Clicking {description} at ({click_x}, {click_y}) [confidence={max_val:.2f}]")
        pyautogui.moveTo(click_x, click_y)
        time.sleep(0.1)
        force_click(click_x, click_y)
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

            if found:
                locate_and_click(play_again_img, "Play Again", get_window_rect(WINDOW_TITLE))
            else:
                print("[INFO] 'Complete' not found. Trying 'Challenge'...")
                if locate_and_click(challenge_img, "Challenge", get_window_rect(WINDOW_TITLE)):
                    time.sleep(2)  # Wait for next UI screen to load
                    locate_and_click(battle_img, "Battle", get_window_rect(WINDOW_TITLE))

                    print("[INFO] Waiting for post-battle screen...")
                    while not locate_and_click(post_battle_img, "Post Battle", get_window_rect(WINDOW_TITLE)):
                        time.sleep(3)

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n[INFO] Script stopped by user.")

if __name__ == "__main__":
    main()
