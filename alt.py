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
import win32gui
import ctypes
import threading

"""
Run this if you wish to only loop the background battles.
It will automatically click 'Play Again' once the background battles are completed.
It will also store a screenshot of the win/loss and items drops acquired in the screenshots folder.
"""

# === CONFIGURATION ===
WINDOW_TITLE = "Etheria:Restart"
THRESHOLD = 0.8
CHECK_INTERVAL = 30


# === Utility: Load template images safely ===
def load_template(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[ERROR] File not found: {path}")
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"[ERROR] Failed to load image: {path}")
    if img.shape[2] == 4:
        img = cv2.cvtColor(
            img, cv2.COLOR_BGRA2BGR
        )  # Convert from BGRA to BGR if needed
    return img


# === Load reference images from /assets ===
try:
    complete_img = load_template("assets/complete.png")
    challenge_img = load_template("assets/challenge.png")
    play_again_img = load_template("assets/play-again.png")
    battle_img = load_template("assets/battle.png")
    post_battle_img = load_template("assets/post-battle.png")
    limit_img = load_template("assets/limit.png")
except Exception as e:
    print(e)
    exit(1)


def bring_window_to_front_no_activate(hwnd):
    # SWP_NOACTIVATE = 0x0010
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        0,
        0,
        0,
        0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
    )
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_NOTOPMOST,
        0,
        0,
        0,
        0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
    )


def get_window_rect(title):
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        print(f"[ERROR] No window found with title: {title}")
        return None
    win = windows[0]
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
    # Get total virtual screen bounds
    virtual_screen_left = ctypes.windll.user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
    virtual_screen_top = ctypes.windll.user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
    virtual_screen_width = ctypes.windll.user32.GetSystemMetrics(
        78
    )  # SM_CXVIRTUALSCREEN
    virtual_screen_height = ctypes.windll.user32.GetSystemMetrics(
        79
    )  # SM_CYVIRTUALSCREEN

    # Check bounds
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
    # Always refresh window position
    rect = get_window_rect(WINDOW_TITLE)
    if rect is None:
        return False
    x, y, w, h = rect

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
        hwnd = gw.getWindowsWithTitle(WINDOW_TITLE)[0]._hWnd
        bring_window_to_front_no_activate(hwnd)
        force_click(click_x, click_y)
        return True
    else:
        print(f"[INFO] {description} not found (confidence={max_val:.2f})")
        return False


def locate_on_screen(template_img, description):
    # Always refresh window position
    rect = get_window_rect(WINDOW_TITLE)
    if rect is None:
        return False

    screenshot_bgr, offset = screenshot_window(WINDOW_TITLE)
    if screenshot_bgr is None:
        return False

    result = cv2.matchTemplate(screenshot_bgr, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= THRESHOLD:
        print(f"[INFO] {description} detected on screen [confidence={max_val:.2f}]")
        return True
    else:
        print(f"[INFO] {description} not found (confidence={max_val:.2f})")
        return False


# === Main Loop ===


def automation_loop():
    print("[INFO] Autoclicker started. Press Ctrl+C to stop.")
    try:
        while True:
            print("[INFO] Checking for 'Complete' button...")
            found = locate_and_click(complete_img, "Complete")
            module_limit = locate_and_click(limit_img, "Limit")

            if found:
                time.sleep(3)

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
            elif module_limit:
                print("[INFO] Module limit reached. Sending ESC key to close alert...")
                time.sleep(1)
            else:
                print("[INFO] 'Complete' not found...")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n[INFO] Automation thread stopped by user.")


if __name__ == "__main__":
    automation_thread = threading.Thread(target=automation_loop, daemon=True)
    automation_thread.start()

    try:
        while True:
            # You can perform other tasks here while automation runs
            # For example, wait for user input
            command = input("[MAIN THREAD] Type 'exit' to stop:\n")
            if command.strip().lower() == "exit":
                print("[MAIN THREAD] Exiting program...")
                break
    except KeyboardInterrupt:
        print("[MAIN THREAD] Stopped by user.")
