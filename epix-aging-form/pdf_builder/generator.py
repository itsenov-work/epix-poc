import json
import os
import fitz

PADDING = 59.5  # 21 mm

SUMMARY_W = 476  # 168 mm
SUMMARY_H = 283  # 100 mm

AGING_STATUS_W = 476  # 168 mm
AGING_STATUS_H = 69  # 24.3 mm
RECOMMENDATIONS_INTRO_W = 476  # 168 mm
RECOMMENDATIONS_INTRO_H = 89  # 31.3 mm
RECOMMENDATIONS_W = 455  # 160.5 mm
RECOMMENDATIONS_H = 74  # 26 mm
RECOMMENDATIONS_OUTRO_W = 476  # 168 mm
RECOMMENDATIONS_OUTRO_H = 119  # 42 mm
CONCLUSION_W = 476  # 168 mm
CONCLUSION_H = 104  # 36.6 mm


def register_fonts(page, fonts_path):
    page.clean_contents()
    page.insert_font(fontfile=os.path.join(fonts_path, "Montserrat-Regular.ttf"), fontname="Montserrat")
    page.insert_font(fontfile=os.path.join(fonts_path, "Montserrat-Bold.ttf"), fontname="Montserrat-Bold")
    page.insert_font(fontfile=os.path.join(fonts_path, "Montserrat-Italic.ttf"), fontname="Montserrat-Italic")


def insert_textbox(page, x, y, w, h, text, fontsize, fontname, align=0):
    rect = fitz.Rect(x, y, x + w, y + h)
    page.insert_textbox(rect, text, fontsize=fontsize, fontname=fontname, align=align)


def read_json(json_path):
    with open(json_path, "r") as json_file:
        data = json.load(json_file)
    return data


def edit_fields(config, output_file_path="generated.pdf"):
    # Move to the directory of the script
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    doc = fitz.open("form_template.pdf")
    fonts_path = "fonts"

    coords = read_json("coords.json")
    prevention_coords = read_json("prevention_coords.json")
    recommendations = read_json("recommendations.json")
    preventions = read_json("preventions.json")
    additional_text = read_json("additional_text.json")

    text_box_offset = coords["subtext"][1] - coords["1"][1]
    overall_level = config["overall"]
    config.pop("overall")

    # Assessment summary
    page = doc[1]
    register_fonts(page, fonts_path)
    image_coords = (coords["image"][0] + 15, coords["image"][1] + 40, coords["image"][2] - 15, coords["image"][3] - 80)
    if overall_level == "good":
        page.insert_image(image_coords, filename="delayed_aging.png")
    elif overall_level == "neutral":
        page.insert_image(image_coords, filename="normal_aging.png")
    else:
        page.insert_image(image_coords, filename="accelerated_aging.png")
    insert_textbox(page,
                   PADDING, coords["aging_status"][1], AGING_STATUS_W, AGING_STATUS_H,
                   additional_text["aging_status"][overall_level],
                   33, "Montserrat",
                   align=1)
    # page.draw_rect(image_coords, color=(1, 0, 0), width=2)  # RGB color format, width in points
    insert_textbox(page,
                   PADDING, coords["summary"][1], SUMMARY_W, SUMMARY_H,
                   additional_text["summary"][overall_level], 12, "Montserrat",
                   align=1)

    page = doc[2]
    register_fonts(page, fonts_path)
    insert_textbox(page,
                   PADDING, coords["recommendations"][1], RECOMMENDATIONS_INTRO_W, RECOMMENDATIONS_INTRO_H,
                   additional_text["recommendations_intro"][overall_level], 12, "Montserrat-Italic",
                   align=1)  # 0 - left, 1 - center, 2 - right

    # Recommendations
    for i, field in enumerate(config):
        # Go to next page
        if i == 4:
            page = doc[3]
            register_fonts(page, fonts_path)

        # Insert title
        page.insert_text((coords[str(i + 1)][0], coords[str(i + 1)][1]),
                         recommendations[field][config[field]]["title"],
                         fontsize=18, fontname="Montserrat-Bold")
        # Insert text
        text_box_x = coords[str(i + 1)][0]
        text_box_y = coords[str(i + 1)][1] + text_box_offset
        insert_textbox(page,
                       text_box_x, text_box_y, RECOMMENDATIONS_W, RECOMMENDATIONS_H,
                       recommendations[field][config[field]]["text"], 12, "Montserrat")

    insert_textbox(page,
                   PADDING, coords["conclusion"][1], RECOMMENDATIONS_OUTRO_W, RECOMMENDATIONS_OUTRO_H,
                   additional_text["recommendations_outro"][overall_level], 12, "Montserrat-Italic",
                   align=1)  # 0 - left, 1 - center, 2 - right

    # Preventions
    page = doc[4]
    register_fonts(page, fonts_path)
    for i in range(13):
        page.insert_text((prevention_coords[str(i + 1)][0], prevention_coords[str(i + 1)][1]),
                         preventions[i], fontsize=14, fontname="Montserrat-Bold")

    insert_textbox(page,
                   PADDING, prevention_coords["final_conclusion"][1], CONCLUSION_W, CONCLUSION_H,
                   additional_text["conclusion"][overall_level], 12, "Montserrat-Italic",
                   align=1)

    doc.save(output_file_path)
    doc.close()


if __name__ == "__main__":
    edit_fields()
