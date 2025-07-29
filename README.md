<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

<p align="center">𝖸𝗎𝗆𝖾𝗄𝗈 ♡ </p>

- Yumeko is a powerful and feature-rich Telegram bot designed to help you manage your groups effortlessly.

<p align="center"><a href="https://t.me/Hunt_WH_Updates"><img src="https://envs.sh/s-n.jpeg" width="300"></a></p>
<p align="center">
    <a href="https://www.python.org/" alt="made-with-python"> <img src="https://img.shields.io/badge/Made%20with-Python-black.svg?style=flat-square&logo=python&logoColor=blue&color=red" /></a>

## Repo Stats

![github card](https://github-readme-stats.vercel.app/api/pin/?username=john-wick00&repo=Yumekoo&theme=dark)


## Requirements 

- Python 3.8+ or 3.7
- [Mongo Db](https://youtu.be/mnvjt_a5JYA)


## Features 

- **Anti Spam!**
- **You Can deploy Upto 10 Clients At a Same Time**
- **Almost 50+ Plugins There adding more Plugins Soon**

# Playwright Web Screenshot Setup Guide

This guide will help you set up the necessary dependencies for the Playwright-based Web Screenshot module.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation Steps

### 1. Install Playwright

```bash
pip install playwright>=1.30.0
```

### 2. Install Browser Engines

After installing the Playwright package, you need to install the browser engines:

```bash
python -m playwright install chromium
```

This will download and install the Chromium browser that Playwright will use for taking screenshots.

### 3. Verify Installation

You can verify that Playwright is working correctly by running:

```python
import asyncio
from playwright.async_api import async_playwright

async def test_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://www.google.com")
        print("Page title:", await page.title())
        await browser.close()

asyncio.run(test_playwright())
```

## Troubleshooting

### Common Issues:

1. **Missing dependencies**: On some Linux systems, you might need additional dependencies. Playwright will usually tell you what's missing, but you can install common dependencies with:
   ```bash
   sudo apt update
   sudo apt install -y libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxcb1 libxkbcommon0 libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2
   ```

2. **Permission issues**: If you encounter permission problems, you might need to run with sudo:
   ```bash
   sudo python -m playwright install chromium
   ```

3. **Timeout errors**: If you're getting timeout errors when taking screenshots, try increasing the `SCREENSHOT_TIMEOUT` constant in the code.

## Advantages of Playwright

Playwright has several advantages over other solutions:

1. **Modern and well-maintained**: Playwright is actively developed by Microsoft.
2. **Cross-browser support**: Although we're using Chromium, Playwright also supports Firefox and WebKit.
3. **Powerful automation**: Playwright has robust capabilities for interacting with web pages.
4. **Good performance**: Playwright is designed to be fast and efficient.

## Support

If you encounter any issues, please open an issue on the GitHub repository or contact the maintainers. 


## VPS/Locally deploy!
```console
senpaiii10@Debian~ $ apt-get -y update
senpaiii10@Debian~ $ sudo apt-get install -y libgl1
senpaiii10@Debian~ $ apt-get -y install git gcc python3-pip python3-venv -y
senpaiii10@Debian~ $ git clone https://github.com/john-wick00/Yumekoo
senpaiii10@Debian~ $ cd Yumekoo
senpaiii10@Debian~ $ python3 -m venv myenv
senpaiii10@Debian~ $ source myenv/bin/activate
senpaiii10@Debian~ $ pip3 install -U -r requirements.txt
senpaiii10@Debian~ $ bash start
```

## Credits 💖
- @Zeroo_Twoo_Bot
- Pyrogram
- Telethon
- Python Telegram Bot



## Support / Channel

<p align="center">𝐒𝐮𝐩𝐩𝐨𝐫𝐭 / 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 ----> </p>

<p align="center"><a href="https://t.me/Domihoes"><img src="https://img.shields.io/badge/ᴛᴇʟᴇɢʀᴀᴍ-𝐒𝐮𝐩𝐩𝐨𝐫𝐭-black?&style=for-the-badge&logo=telegram" width="220" height="38.45"></a></p>
<p align="center"><a href="https://t.me/Hunt_WH_Updates"><img src="https://img.shields.io/badge/ᴛᴇʟᴇɢʀᴀᴍ-𝐔𝐩𝐝𝐚𝐭𝐞𝐬-black?&style=for-the-badge&logo=telegram" width="220" height="38.45"></a></p>
