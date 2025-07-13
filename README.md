# 🔁 Etheria AutoClicker

This is a Python-based automation tool for the game **Etheria:Restart**. It automates both **foreground and background battles**, with optional screenshot logging, post-battle decision handling, and win/loss tracking.

## 📁 Scripts

### `main.py`
- Loops **both background and foreground battles**.
- Logs battle results (`WIN`/`LOSS`) to `screenshots/log.txt`.
- Saves battle result screenshots in the `screenshots/` folder.
- Handles additional clicks for post-battle screens.

### `alt.py`
- Focuses **only on background battles**.
- Automatically clicks `Play Again` when the battle is complete.
- Captures a screenshot of each result and saves it in `screenshots/`.

---

## ⚙️ Requirements

Ensure you're using **Python 3.8+** and have the following packages installed:

```
pyautogui
pygetwindow
opencv-python
numpy
mss
pywin32
```

You can install all dependencies using:

```bash
pip install -r requirements.txt
```

---

## ⚠️ Important Notes

- 🧠 **Run as Administrator**
  The script needs elevated permissions to move the mouse and click on game windows. **Right-click your terminal or IDE and choose "Run as administrator."**

- 🖥️ **Game Must Be Fullscreen**
  The script relies on image matching. Fullscreen ensures consistent visuals.

- 📌 **Image Assets Required**
  Make sure the following image files exist in a folder named `assets/`:
  ```
  assets/
    ├── complete.png
    ├── challenge.png
    ├── play-again.png
    ├── battle.png
    ├── post-battle.png
    └── fail.png
  ```

- 📷 **Screenshots Folder**
  Screenshots will be saved to `screenshots/`, and a log file (`log.txt`) will track wins/losses when using `main.py`.

---

## ▶️ How to Run

1. Open terminal or your IDE **with administrator rights**.
2. Ensure the game is **running in fullscreen mode**.
3. Choose a script based on your use case:
   - Background-only battles:
     ```bash
     python alt.py
     ```
   - Full loop (bg + fg battles):
     ```bash
     python main.py
     ```

4. Stop the script anytime with **Ctrl+C**.

---

## 📊 Logs

When using `main.py`, battle outcomes are recorded in:
```
screenshots/log.txt
```

To see the current tally of wins and losses, `main.py` will print it automatically, or you can call the `summarize_log()` function manually.

---

## 🧪 Tested On

- Windows 10 / 11
- Python 3.10+
- Game: **Etheria:Restart**

---

Feel free to customize the `assets/` folder or adjust the `THRESHOLD` and `CHECK_INTERVAL` in each script to better fit your screen resolution or game version.