import pygetwindow as gw
import time
import cv2
import numpy as np
import pyautogui
import os
from datetime import datetime
import mss
import win32api
import win32con
import ctypes

# === CONFIGURATION ===
WINDOW_TITLE = "Etheria:Restart"
THRESHOLD = 0.8
CHECK_INTERVAL = 4


# === Utility: Load template images safely ===
def load_template(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[ERROR] File not found: {path}")
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"[ERROR] Failed to load image: {path}")
    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


# === Load reference images from /assets ===
try:
    complete_img = load_template("assets/complete.png")
    challenge_img = load_template("assets/challenge.png")
    play_again_img = load_template("assets/play-again.png")
    battle_img = load_template("assets/battle.png")
    post_battle_img = load_template("assets/post-battle.png")
    elimination_img = load_template("assets/fail.png")
except Exception as e:
    print(e)
    exit(1)


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
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": w, "height": h}
            sct_img = sct.grab(monitor)
            img = np.array(sct_img)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img, (x, y)
    return None, (0, 0)


def force_click(x, y):
    virtual_screen_left = ctypes.windll.user32.GetSystemMetrics(76)
    virtual_screen_top = ctypes.windll.user32.GetSystemMetrics(77)
    virtual_screen_width = ctypes.windll.user32.GetSystemMetrics(78)
    virtual_screen_height = ctypes.windll.user32.GetSystemMetrics(79)

    if not (
        virtual_screen_left <= x <= virtual_screen_left + virtual_screen_width
        and virtual_screen_top <= y <= virtual_screen_top + virtual_screen_height
    ):
        print(f"[ERROR] Click ({x}, {y}) is outside the virtual screen bounds")
        return

    win32api.SetCursorPos((x, y))
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def locate_and_click(template_img, description):
    rect = get_window_rect(WINDOW_TITLE)
    if rect is None:
        return False

    screenshot_bgr, offset = screenshot_window(WINDOW_TITLE)
    if screenshot_bgr is None:
        return False

    result = cv2.matchTemplate(screenshot_bgr, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= THRESHOLD:
        h_temp, w_temp = template_img.shape[:2]
        click_x = offset[0] + max_loc[0] + w_temp // 2
        click_y = offset[1] + max_loc[1] + h_temp // 2

        print(
            f"[INFO] Clicking {description} at ({click_x}, {click_y}) [confidence={max_val:.2f}]"
        )
        win = gw.getWindowsWithTitle(WINDOW_TITLE)[0]
        win.activate()
        time.sleep(0.1)
        force_click(click_x, click_y)
        return True
    return False


def locate_on_screen(template_img, description):
    rect = get_window_rect(WINDOW_TITLE)
    if rect is None:
        return False

    screenshot_bgr, offset = screenshot_window(WINDOW_TITLE)
    if screenshot_bgr is None:
        return False

    result = cv2.matchTemplate(screenshot_bgr, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)

    if max_val >= THRESHOLD:
        print(f"[INFO] {description} detected on screen [confidence={max_val:.2f}]")
        return True
    return False


def summarize_log():
    win_count = 0
    loss_count = 0

    try:
        with open("screenshots/log.txt", "r") as file:
            for line in file:
                if line.strip().upper() == "WIN":
                    win_count += 1
                elif line.strip().upper() == "LOSS":
                    loss_count += 1
    except FileNotFoundError:
        print("Log file not found.")
        return

    print(f"Win: {win_count}")
    print(f"Loss: {loss_count}")


def main():
    print("[INFO] Autoclicker started. Press Ctrl+C to stop.")
    try:
        while True:
            print("[INFO] Checking for Background Battles...")
            found = locate_and_click(complete_img, "Complete")
            next_battle = locate_and_click(challenge_img, "Challenge")

            if found:
                time.sleep(2)
                screenshot_dir = "screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                screenshot_path = os.path.join(
                    screenshot_dir, f"screenshot_{timestamp}.png"
                )
                screenshot = pyautogui.screenshot()
                screenshot.save(screenshot_path)
                print(f"[INFO] Screenshot saved to {screenshot_path}")

                while not locate_and_click(play_again_img, "Play Again"):
                    time.sleep(1)

            elif next_battle:
                time.sleep(2)
                while not locate_and_click(battle_img, "Battle"):
                    time.sleep(1)
                summarize_log()
                print("[INFO] Waiting for post-battle screen...")
                while True:
                    found_post = locate_on_screen(post_battle_img, "Post Battle")
                    try:
                        found_elimination = locate_on_screen(elimination_img, "Failed")
                    except:
                        found_elimination = False

                    if found_post:
                        print(
                            "[INFO] Post-battle detected, doing extra click to dismiss..."
                        )
                        with open("screenshots/log.txt", "a") as file:
                            file.write("WIN\n")
                        time.sleep(3)
                        rect = get_window_rect(WINDOW_TITLE)
                        if rect:
                            center_x = rect[0] + rect[2] // 2
                            center_y = rect[1] + rect[3] // 2
                            force_click(center_x, center_y)
                        break
                    if found_elimination:
                        print("Run failed.")
                        with open("screenshots/log.txt", "a") as file:
                            file.write("LOSS\n")
                        time.sleep(3)
                        rect = get_window_rect(WINDOW_TITLE)
                        if rect:
                            center_x = rect[0] + rect[2] // 2
                            center_y = rect[1] + rect[3] // 2
                            force_click(center_x, center_y)
                        break
                    else:
                        time.sleep(5)

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n[INFO] Script stopped by user.")


if __name__ == "__main__":
    main()
