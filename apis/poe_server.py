import os

from poe_api_wrapper import AsyncPoeApi
import asyncio

# Function to read and parse the cookies file
def read_cookies(file_path):
    cookies = {}
    with open(file_path, 'r') as file:
        for line in file:
            if '#' in line:
                continue  # Skip comments
            parts = line.strip().split('\t')
            if len(parts) >= 7:
                domain, include_subdomains, path, secure, expiration, name, value = parts[:7]
                cookies[name] = value
    return cookies

# Path to your cookies file
cookies_file_path = 'cookies.txt'

# Read and parse the cookies file
cookies = read_cookies(cookies_file_path)

# Extract the necessary tokens
tokens = {
    'p-b': cookies.get('p-b'),
    'p-lat': cookies.get('p-lat'),
}

async def main():
    client = await AsyncPoeApi(tokens=tokens).create()
    bot    = "gemini_1_5_pro_128k"

    file_urls = [
        "https://arxiv.org/pdf/2409.20537",]
    local_files = []
    # download the files to `tmp_files/`
    os.makedirs("tmp_files", exist_ok=True)
    for file_url in file_urls:
        if file_url.startswith("http"):
            file_name = file_url.split("/")[-1]
            if "arxiv" in file_url:
                file_name = file_name + ".pdf"
            file_path = f"tmp_files/{file_name}"
            # wget -O file_path file_url
            os.system(f"wget -O {file_path} {file_url}")
            local_files.append(file_path)
    
    async for chunk in client.send_message(bot, "Summarize", file_path=local_files):
        print(chunk["response"], end="", flush=True)

    # continue the conversation
    message = "What is the best book in this field?"
    async for chunk in client.send_message(bot=bot, message=message, chatCode=chunk["chatCode"]):
        print(chunk["response"], end='', flush=True)

asyncio.run(main())
