import json
import os
import fitz


def extract_text_and_font(pdf_path="EPIX Assessment PDF.pdf", pages=[1, 2, 3, 4]):
    text_with_font = {}
    for page_num in pages:
        text_with_font[page_num] = []

    doc = fitz.open(pdf_path)

    for page_num in pages:
        page = doc[page_num]
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    text_with_font[page_num].append(
                        (span["text"], span["bbox"], (span["font"], span["size"], span["flags"])))

    return text_with_font


def write_text_with_font(output_pdf_path, text_with_font, pages=[1, 2, 3, 4]):
    doc = fitz.open("EPIX Assessment PDF Template with numbers.pdf")
    result_with_image = fitz.open("EPIX Assessment PDF.pdf")
    fonts_path = "fonts"

    prevention_coords = []
    prevention_coords_dict = {}
    prevention_line = 0
    coords = {}
    for page_num in pages:
        page = doc[page_num]
        if page_num == 1 and "image" not in coords:
            temp_page = result_with_image[page_num]
            temp_page.clean_contents()
            d = temp_page.get_text("dict")
            blocks = d["blocks"]  # the list of block dictionaries
            imgblocks = [b["bbox"] for b in blocks if b["type"] == 1]
            coords["image"] = list(imgblocks[1])
        page.clean_contents()
        for text, bbox, font in text_with_font[page_num]:
            bbox = list(bbox)
            bbox[1] += font[1]

            if page_num == 1:
                if text == "Normal Aging":
                    coords["aging_status"] = [bbox[0], bbox[1] - font[1]]

                if text.startswith("Your results indicate a notably positive"):
                    coords["summary"] = [bbox[0], bbox[1] - font[1]]
            elif page_num == 2:
                if text.startswith("Given the positive biological aging"):
                    coords["recommendations"] = [bbox[0], bbox[1] - font[1]]

                if text.startswith("Maintain your engagement in moderate"):
                    coords["subtext"] = [bbox[0], bbox[1] - font[1]]

                if text.startswith("Continue Regular"):
                    coords["1"] = [bbox[0], bbox[1]]

                if text.startswith("Optimize Diet"):
                    coords["2"] = [bbox[0], bbox[1]]

                if text.startswith("Maintain Healthy"):
                    coords["3"] = [bbox[0], bbox[1]]

                if text.startswith("Prioritize Adequate"):
                    coords["4"] = [bbox[0], bbox[1]]
            elif page_num == 3:
                if text.startswith("By maintaining these positive habits"):
                    coords["conclusion"] = [bbox[0], bbox[1] - font[1]]

                if text.startswith("Stay Proactive"):
                    coords["5"] = [bbox[0], bbox[1]]

                if text.startswith("Regular Health Check"):
                    coords["6"] = [bbox[0], bbox[1]]

                if text.startswith("Explore Additional Wellness"):
                    coords["7"] = [bbox[0], bbox[1]]

                if text.startswith("Encourage Healthy Lifestyle"):
                    coords["8"] = [bbox[0], bbox[1]]
            elif page_num == 4:
                if 100 <= bbox[1] <= 650:
                    prevention_coords.append([bbox[0], bbox[1]])

                if text.startswith("Integrating these additional measures"):
                    prevention_coords_dict["final_conclusion"] = [bbox[0], bbox[1] - font[1]]

            # page.insert_text((bbox[0], bbox[1]+20), text, fontsize=font[1], fontname=font[0])
            page.insert_font(fontfile=os.path.join(fonts_path, font[0] + ".ttf"), fontname=font[0])
            page.insert_text((bbox[0], bbox[1]), text, fontsize=font[1], fontname=font[0])

    prevention_coords = sorted(prevention_coords, key=lambda x: x[1])
    for i, coordinates in enumerate(prevention_coords):
        prevention_coords_dict[i + 1] = coordinates

    with open("coords.json", "w") as json_file:
        json.dump(coords, json_file, indent=4)

    with open("prevention_coords.json", "w") as json_file:
        json.dump(prevention_coords_dict, json_file, indent=4)

    doc.save(output_pdf_path)
    doc.close()


if __name__ == "__main__":
    extracted_text_with_font = extract_text_and_font()
    write_text_with_font("output.pdf", extracted_text_with_font)
