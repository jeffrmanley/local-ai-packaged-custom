import fitz  # PyMuPDF
from flask import Flask, request, jsonify
import io

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file_storage = request.files['file']
    pdf_data = file_storage.read()

    try:
        # Open the PDF with PyMuPDF
        pdf_file = fitz.open(stream=pdf_data, filetype="pdf")

        # Extract text
        all_text = []
        all_links = []

        for page_index in range(len(pdf_file)):
            page = pdf_file[page_index]
            # Extract text from each page
            all_text.append(page.get_text())

            # Extract link annotations
            link_dicts = page.get_links()
            for lnk in link_dicts:
                if "uri" in lnk:
                    all_links.append(lnk["uri"])

        pdf_file.close()

        # Combine text from all pages
        text = "\n".join(all_text)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "text": text,
        "links": all_links
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
