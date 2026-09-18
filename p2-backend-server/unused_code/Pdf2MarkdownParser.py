import os.path

import spacy
from spacy_layout import spaCyLayout

import os
import re

import fitz
from PIL import Image

# The parsing of a markdown File
# Unsure if it is working (did not test it)
class Pdf2MarkdownParser:
    def __init__(self):
        self.nlp = spacy.blank("de")
        self.layout = spaCyLayout(self.nlp)

    def parse(self, file, path):
        file_path = os.path.join(path, filename)
        filename_wo_ending = os.path.splitext(filename)[0]
        print(f'parse file {filename}')
        doc = self.layout(file_path)
        self.pdf2md(p, doc, filename_wo_ending)
        #self.get_pdf_imgs(p, file_path, filename_wo_ending)

    def get_pdf_imgs(self, img_path, pathfilename, filename):
        # open the file
        pdf_file = fitz.open(pathfilename)
        img_path = os.path.join(img_path, filename)
        # iterate over PDF pages
        for page_index in range(len(pdf_file)):

            # get the page itself
            page = pdf_file.load_page(page_index)  # load the page
            image_list = page.get_images(full=True)  # get images on the page

            # printing number of images found in this page
            if image_list:
                print(f"[+] Found a total of {len(image_list)} images on page {page_index}")
            else:
                print("[!] No images found on page", page_index)

            for image_index, img in enumerate(image_list, start=1):
                if not os.path.exists(img_path):
                    os.mkdir(img_path)
                # get the XREF of the image
                xref = img[0]

                # extract the image bytes
                base_image = pdf_file.extract_image(xref)
                image_bytes = base_image["image"]

                # get the image extension
                image_ext = base_image["ext"]

                # save the image
                image_name = os.path.join(img_path, f"image_{page_index+1}_{image_index}.{image_ext}")
                with open(image_name, "wb") as image_file:
                    image_file.write(image_bytes)
                    print(f"[+] Image saved as {image_name}")

    def clean_legal_texts(self, markdown_text):
        lines = markdown_text.splitlines()
        formatted_lines = []

        # Regulärer Ausdruck, um Paragraphen zu finden (z.B. "§ 1" oder "§ 1.1")
        section_pattern = re.compile(r"^§\s\d+(?:\.\d+)?$")

        # Regulärer Ausdruck, um Überschriften zu finden (z.B. "## Titel" oder "### Titel")
        heading_pattern = re.compile(r"^(#+)\s*(.*)$")

        current_section = None

        for i, line in enumerate(lines):
            # Prüfen, ob die Zeile eine Paragraphennummer ist
            section_match = section_pattern.match(line.strip())
            # Prüfen, ob die Zeile eine Überschrift ist
            heading_match = heading_pattern.match(line.strip())

            if section_match:
                current_section = line.strip()

            elif line.strip() == '' and current_section:
                pass

            elif heading_match and current_section:
                heading_level = heading_match.group(1)  # z.B. ## oder ###
                heading_text = heading_match.group(2)  # z.B. Anwendungsbereich

                # Die neue formatierte Zeile erstellen
                new_line = f"{heading_level} {current_section} {heading_text}"
                formatted_lines.append(new_line)

                # Die Paragraphennummer zurücksetzen, damit sie nicht für die nächste Überschrift
                # wiederverwendet wird
                current_section = None
            else:
                # Andere Zeilen unverändert beibehalten
                formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def pdf2md(self, doc_path, doc, filename):
        path = os.path.join(doc_path, 'parsed_mds')
        if not os.path.exists(path):
            os.mkdir(path)

        filename = os.path.join(path, f'{filename}.md')
        print(f"Saving Markdown {filename}")
        file = open(filename, 'w')
        markdown = doc._.markdown
        if '§' in markdown:
            markdown = self.clean_legal_texts(markdown)
        file.write(markdown)
        file.close()

if __name__ == "__main__":
    p = os.path.join('.', 'data', 'fb11_data')
    files = [f for f in os.listdir(p) if os.path.isfile(os.path.join(p, f)) and f.endswith('.pdf')]
    parser = Pdf2MarkdownParser()
    # Process a document and create a spaCy Doc object
    for filename in files:
        if filename.endswith('.pdf'):
            print(f'📕 Parsing pdf {filename}')
            parser.parse(filename, p)
