import requests


try:
    # выставите свой порт
    direct_access = {
        "http": "socks5h://127.0.0.1:7890",
        "https": "socks5h://127.0.0.1:7890"
    }

    proxy = {
        "http": "socks5h://127.0.0.1:7891",
        "https": "socks5h://127.0.0.1:7891"
    }
    print("По умолчанию:",requests.get("https://api.ipify.org").text)

    response_standart = requests.get("https://httpbin.org/ip", proxies=direct_access, timeout=15)
    print("Напрямую:", response_standart.json())

    response_proxy = requests.get("https://httpbin.org/ip", proxies=proxy, timeout=15)
    print("Через прокси:", response_proxy.json())
except Exception as e:
    print(f"Error: {e}")
    print(requests.get("https://api.ipify.org").text)
