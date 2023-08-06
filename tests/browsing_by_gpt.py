import requests
from bs4 import BeautifulSoup

# Send a GET request to the webpage
url = "https://www.rockwellautomation.com/en-us/company/investor-relations/events-presentations.html"
response = requests.get(url)

# Create a BeautifulSoup object to parse the HTML content
soup = BeautifulSoup(response.content, "html.parser")

# Find and extract meaningful text elements from the webpage
text_elements = soup.find_all(text=True)

# Filter out unnecessary whitespace and script/style tags
meaningful_text = [element.strip() for element in text_elements if element.parent.name not in ["script", "style"]]

# Join the extracted text elements into a single string
result = " ".join(meaningful_text)

# Print the resulting text
print(result)

   