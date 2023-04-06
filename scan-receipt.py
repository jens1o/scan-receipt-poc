import cv2
import pytesseract
import datetime
import re
from symspellpy import SymSpell, Verbosity
from pathlib import Path
from PIL import Image

AMOUNT_REGEX = re.compile("^(-)?[0-9]{1,},[0-9]{2}")

sym_spell = SymSpell(max_dictionary_edit_distance=4, prefix_length=7)

# term_index is the column of the term and count_index is the
# column of the term frequency
sym_spell.load_dictionary("dictionary.txt", term_index=0, count_index=1)

def print_receipt_data(file_path: str):
    image = cv2.imread(file_path)

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    tesseract_data = pytesseract.image_to_data(Image.fromarray(image), lang='DEU', output_type='dict')

    image_height, image_width = image.shape

    same_line_data = {
        "last_word_num": None,
        "text_content": "",
        "left": image_width,
        "right": 0,
        "top": image_height,
        "bottom": 0,
    }

    for i in range(len(tesseract_data['left'])):
        confidence = tesseract_data['conf'][i]

        if confidence < 5:
            continue

        text = tesseract_data['text'][i].strip()

        if text == '':
            continue

        word_num = tesseract_data['word_num'][i]

        if same_line_data['last_word_num'] is None:
            same_line_data['last_word_num'] = word_num
        else:
            if word_num < same_line_data['last_word_num']:
                left = same_line_data['left']
                top = same_line_data['top']
                cv2.rectangle(image, (left, top), (same_line_data['right'], same_line_data['bottom']), (0, 255, 0), 3)
                text_content = same_line_data['text_content']
                cv2.putText(image, f'{text_content}', (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

                # line break -> reset
                same_line_data = {
                    "last_word_num": None,
                    "text_content": "",
                    "left": image_width,
                    "right": 0,
                    "top": image_height,
                    "bottom": 0,
                }

            same_line_data['last_word_num'] = word_num


        suggestions = sym_spell.lookup(
            text, Verbosity.CLOSEST, max_edit_distance=2, include_unknown=True
        )

        if text != suggestions[0].term:
            print(f"replacing {text} -> {suggestions[0].term}")

        same_line_data['text_content'] += suggestions[0].term + ' '


        left = tesseract_data['left'][i]
        top = tesseract_data['top'][i]
        height = tesseract_data['height'][i]
        width = tesseract_data['width'][i]

        right = left+width
        bottom = top+height

        same_line_data['left'] = min(left, same_line_data['left'])
        same_line_data['right'] = max(right, same_line_data['right'])
        same_line_data['top'] = min(top, same_line_data['top'])
        same_line_data['bottom'] = max(bottom, same_line_data['bottom'])

    isodatetime = datetime.datetime.now().isoformat()
    cv2.imwrite(f"results/result-{isodatetime}.png", image)

    # cv2.imshow("result", image)
    # cv2.waitKey()

for path in Path('assets').rglob('*.*'):
    print_receipt_data('assets/' + path.name)
