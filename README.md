<p align="right">
  <a href="README.ru.md">🇷🇺 Перейти на русскую версию</a>
</p>

# 📦 Kaguya UserBot Official Modules & Addons

A curated directory of official and community-submitted custom modules for **Kaguya UserBot**. 

---

## 📥 Installation Guide

To install any of the modules listed below, simply send its raw file to your running userbot in Telegram:

1. Open the file you want to install from the `modules/` directory.
2. Click the **Raw** button in the upper right corner of the file preview.
3. Save the page as a `.py` file (e.g. `Ctrl+S` or via your browser menu).
4. Send this `.py` file to yourself or to any chat in Telegram.
5. Reply to the uploaded file with the command `.install` (or `.установить`).

---

## 🛠️ How to Publish Your Module (For Developers)

We welcome any community-made modules! If you've developed a custom plug-in and want to share it, please submit a Pull Request following these guidelines.

### Code Quality and Standards:
* The module must inherit from `BaseModule` and define a valid `ModuleInfo` object.
* It must support internationalization (i18n) via the class-level `LANGUAGES` dictionary and retrieve strings using `self.get_text("key")`.
* Import any external dependencies (not present in the core `requirements.txt`) gracefully:
  ```python
  try:
      import some_library
  except ImportError:
      raise ImportError("This module requires 'some_library'. Install it via: pip install some_library")
  ```
* Code must be readable and thoroughly commented. Obfuscation, malicious system calls (unapproved `eval`, `exec`, shell subprocess execution), and sneaky transmission of session files (`.session`) or bot tokens are strictly prohibited and will be blocked by review.

### Submission Workflow:
1. **Fork** this repository.
2. Copy your `.py` module file (or module package folder) into the `modules/` directory.
3. Register your module and its metadata inside the root `index.json` file.
4. Submit a **Pull Request** to our main branch with a brief description of what your plugin does.
5. After a manual code audit, your module will be merged and listed in our official registry!
