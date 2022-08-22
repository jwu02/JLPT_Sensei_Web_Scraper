import random
from typing import List
import genanki
from jlptsensei_scraper import dir_exists
import csv


def get_model() -> genanki.Model:
    """
    Return a model which defines the fields and cards for a type of note
    """
    # generate a unique model id
    model_id = random.randrange(1 << 30, 1 << 31)

    my_model = genanki.Model(
        model_id,
        'Knowledge',
        fields=[
            {'name': 'Index'},
            {'name': 'Vocabulary'},
            {'name': 'Reading'},
            {'name': 'Meaning'},
        ],
        templates=[{
            'name': 'JLPT Vocabulary',
            'qfmt': '{{Vocabulary}}',
            'afmt': '{{FrontSide}}<hr id="answer">{{Reading}}<br>{{Meaning}}',
        },]
    )

    return my_model


def generate_deck() -> genanki.Deck:
    """
    Read CSV file and convert each row into an Anki card
    """
    my_model = get_model()
    
    deck_id = random.randrange(1 << 30, 1 << 31)
    my_deck = genanki.Deck(deck_id, "JLPT NX Vocabulary")

    with open("./data/n1_vocabulary_list.csv", encoding="utf8") as vocab_csv:
        vocab_csv_reader = csv.reader(vocab_csv, delimiter=',')
        next(vocab_csv_reader) # skip column headings

        for row in vocab_csv_reader:
            print(row)
            vocab_index, vocab, vocab_reading, vocab_type, vocab_meaning = list(row)
            my_note = genanki.Note(
                model=my_model,
                fields=[f'{vocab_index}', f'{vocab}', f'{vocab_reading}', f'{vocab_meaning}'],
                tags=process_vocab_type_tags(vocab_type)
            )

            my_deck.add_note(my_note)
    
    return my_deck


def process_vocab_type_tags(vocab_type: str) -> List[str]:
    """
    Convert vocab types into valid note tags which can't contain spaces
    """
    return [v.replace(" ", "_").lower() for v in vocab_type.split(", ")]


def save_deck(deck: genanki.Deck) -> None:
    outdir = "./data/decks"
    dir_exists(outdir)

    deck_file = outdir + f"/JLPT_Vocabulary_NX.apkg"
    genanki.Package(deck).write_to_file(deck_file)


if __name__ == "__main__":
    save_deck(generate_deck())