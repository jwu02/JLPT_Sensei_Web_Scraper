import random
from typing import List
import genanki
import csv

from jlptsensei_scraper import JLPT_LEVELS
from jlptsensei_scraper import dir_exists


def get_vocabulary_model() -> genanki.Model:
    """
    Return a model which defines the fields and cards for a type of note
    """
    # generate a unique model id
    model_id = random.randrange(1 << 30, 1 << 31)

    # read template html and css files to assign to model properties
    with open("template/vocab_recognition_front.html", "r") as f:
        front_template_html = f.read()
    with open("template/vocab_recognition_back.html", "r") as f:
        back_template_html = f.read()
    with open("template/vocab_recognition.css", "r") as f:
        template_css = f.read()

    my_model = genanki.Model(
        model_id,
        'JLPT Sensei Vocabulary',
        fields=[
            {'name': 'Vocabulary'},
            {'name': 'Reading'},
            {'name': 'Meaning'},
            {'name': 'Sentence JP'},
            {'name': 'Sentence EN'},
            {'name': 'Index'}
        ],
        templates=[{
            'name': 'Vocabulary Recognition',
            'qfmt': front_template_html,
            'afmt': back_template_html,
        },],
        css=template_css,
    )

    return my_model


def generate_vocabulary_deck(vocab_model: genanki.Model, jlpt_level: str) -> genanki.Deck:
    """
    Read CSV file and convert each row into an Anki card
    """

    print(f"Generating {jlpt_level.upper()} Vocabulary Deck...", end="\r")

    deck_id = random.randrange(1 << 30, 1 << 31)
    vocab_deck = genanki.Deck(deck_id, f"JLPT Sensei {jlpt_level.upper()} Vocabulary")

    with open(f"./data/vocabulary/{jlpt_level}_vocabulary_list.csv", encoding="utf8") as vocab_csv:
        vocab_csv_reader = csv.reader(vocab_csv, delimiter=',')
        next(vocab_csv_reader) # skip column headings

        for row in vocab_csv_reader:
            v_index, vocab, v_reading, v_type, v_meaning, v_sentence_jp, v_sentence_en = list(row)
            vocab_note = genanki.Note(
                model=vocab_model,
                fields=[vocab, v_reading, v_meaning, v_sentence_jp, v_sentence_en, v_index],
                tags=process_vocab_type_tags(v_type)
            )

            vocab_deck.add_note(vocab_note)
    
    return vocab_deck


def process_vocab_type_tags(vocab_type: str) -> List[str]:
    """
    Convert vocab types into valid note tags which can't contain spaces
    """
    vt_list = vocab_type.split(", ")
    for i in range(len(vt_list)):
        vt_list[i] = vt_list[i].replace(" ", "_").lower()
        vt_list[i] = "JLPT_Sensei::" + vt_list[i]

    return vt_list


def save_deck(deck: genanki.Deck, jlpt_level: str) -> None:
    outdir = "./data/decks"
    dir_exists(outdir)

    deck_file = outdir + f"/JLPT_Sensei_{jlpt_level.upper()}_Vocabulary.apkg"
    genanki.Package(deck).write_to_file(deck_file)

    print(f"Finished generating {jlpt_level.upper()} Vocabulary Deck!")


if __name__ == "__main__":
    # JLPT_LEVELS = ['n5']

    vocab_model = get_vocabulary_model()
    for level in JLPT_LEVELS:
        vocab_deck = generate_vocabulary_deck(vocab_model, level)
        save_deck(vocab_deck, level)
    
    print("Finished generating anki decks.")