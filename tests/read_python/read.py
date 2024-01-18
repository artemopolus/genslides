import PyPDF2
import sys

def read_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)

        for page_number in range(len(pdf.pages)):
            page = pdf.pages[page_number]
            text = page.extract_text()
            print(text)

def main():
    # Check if a file path is provided as an argument
    if len(sys.argv) < 2:
        print("Please provide the path to a PDF file.")
        return

    pdf_file_path = sys.argv[1]
    read_pdf(pdf_file_path)

if __name__ == '__main__':
    main()
