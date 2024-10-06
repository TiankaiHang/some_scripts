import asyncio
from gemini_webapi import GeminiClient

def load_cookies_from_file(file_path):
    cookies = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if not line.startswith('#') and line.strip():
                    fields = line.strip().split('\t')
                    if len(fields) >= 7:
                        domain = fields[0]
                        name = fields[5]
                        value = fields[6]
                        cookies[name] = {'domain': domain, 'value': value}
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    return cookies

async def main():
    # Load cookies from file
    cookies_dict = load_cookies_from_file('cookies.txt')
    
    # Extract the required cookies
    Secure_1PSID = cookies_dict.get('__Secure-1PSID', {}).get('value', '')
    Secure_1PSIDTS = cookies_dict.get('__Secure-1PSIDTS', {}).get('value', '')
    
    if not Secure_1PSID:
        print("Error: __Secure-1PSID cookie not found in cookies.txt")
        return
    
    # Initialize GeminiClient with the extracted cookies
    client = GeminiClient(Secure_1PSID, Secure_1PSIDTS, proxies=None)
    await client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True)
    
    # Here you can add your code to use the client
    # For example:
    response = await client.generate_content("帮我写一篇关于Python的文章，over 1000 words")
    print(response.text)
    
    # Don't forget to close the client when you're done
    await client.close()

asyncio.run(main())