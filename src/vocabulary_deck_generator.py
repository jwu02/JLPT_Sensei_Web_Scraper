import random
from typing import List
import csv
import genanki

from anki_deck_generator import AnkiDeckGenerator


class VocabularyDeckGenerator(AnkiDeckGenerator):
    def __init__(self, level: str) -> None:
        super().__init__(level)
        self.LESSON_TYPE = 'vocabulary'


    def generate_model(self) -> None:
        # generate a unique model id
        model_id = random.randrange(1 << 30, 1 << 31)

        # read template html and css files to assign to model properties
        with open(f'template/{self.LESSON_TYPE}_recognition_front.html', 'r') as f:
            front_template_html = f.read()
        with open(f'template/{self.LESSON_TYPE}_recognition_back.html', 'r') as f:
            back_template_html = f.read()
        with open(f'template/{self.LESSON_TYPE}_recognition.css', 'r') as f:
            template_css = f.read()

        vocab_model = genanki.Model(
            model_id,
            f'JLPT Sensei {self.LESSON_TYPE.capitalize()}',
            fields=[
                {'name': 'Vocabulary'},
                {'name': 'Reading'},
                {'name': 'Meaning'},
                {'name': 'Sentence JP'},
                {'name': 'Sentence EN'},
                {'name': 'Notes'},
                {'name': 'Index'}
            ],
            templates=[{
                'name': 'Vocabulary Recognition',
                'qfmt': front_template_html,
                'afmt': back_template_html,
            },],
            css=template_css,
        )

        self.anki_model = vocab_model


    def generate_deck(self) -> None:
        print(f"Generating {self.jlpt_level.capitalize()} {self.LESSON_TYPE} deck...", end='\r')

        deck_id = random.randrange(1 << 30, 1 << 31)
        vocab_deck = genanki.Deck(deck_id, f'JLPT Sensei {self.jlpt_level.upper()} {self.LESSON_TYPE.capitalize()}')

        with open(f'./data/{self.LESSON_TYPE}/{self.jlpt_level}_{self.LESSON_TYPE}_list.csv', encoding='utf8') as vocab_csv:
            vocab_csv_reader = csv.reader(vocab_csv, delimiter=',')
            next(vocab_csv_reader) # skip column headings

            for row in vocab_csv_reader:
                v_index, vocab, v_reading, v_type, v_meaning, v_sentence_jp, v_sentence_en = list(row)
                vocab_note = genanki.Note(
                    model=self.anki_model,
                    fields=[vocab, v_reading, v_meaning, v_sentence_jp, v_sentence_en, '', v_index],
                    tags=self.process_vocab_type_tags(v_type)
                )

                vocab_deck.add_note(vocab_note)
        
        self.anki_deck = vocab_deck


    def process_vocab_type_tags(self, vocab_type: str) -> List[str]:
        """
        Convert vocab types into valid note tags which can't contain spaces
        """
        vt_list = vocab_type.split(', ')
        for i in range(len(vt_list)):
            vt_list[i] = vt_list[i].replace(' ', '_').lower()
            vt_list[i] = 'JLPT_Sensei::' + vt_list[i]

        return vt_list
    

    def main(self):
        self.generate_model()
        self.generate_deck()
        self.save_deck()
