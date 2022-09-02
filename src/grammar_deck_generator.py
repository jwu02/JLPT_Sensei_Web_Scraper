import random
import csv
import genanki

from src.anki_deck_generator import AnkiDeckGenerator


class GrammarDeckGenerator(AnkiDeckGenerator):
    def __init__(self, level: str) -> None:
        super().__init__(level)
        self.LESSON_TYPE = 'grammar'


    def generate_model(self) -> None:
        # generate a unique model id
        model_id = random.randrange(1 << 30, 1 << 31)

        # read template html and css files to assign to model properties
        with open(f'src/template/{self.LESSON_TYPE}_recognition_front.html', 'r') as f:
            front_template_html = f.read()
        with open(f'src/template/{self.LESSON_TYPE}_recognition_back.html', 'r') as f:
            back_template_html = f.read()
        with open(f'src/template/{self.LESSON_TYPE}_recognition.css', 'r') as f:
            template_css = f.read()

        grammar_model = genanki.Model(
            model_id,
            f'JLPT Sensei {self.LESSON_TYPE.capitalize()}',
            fields=[
                {'name': 'Grammar'},
                {'name': 'Reading'},
                {'name': 'Meaning'},
                {'name': 'Sentence JP'},
                {'name': 'Sentence EN'},
                {'name': 'Notes'},
                {'name': 'Flashcard Image'},
                {'name': 'Source'},
                {'name': 'Index'},
            ],
            templates=[{
                'name': 'Grammar Recognition',
                'qfmt': front_template_html,
                'afmt': back_template_html,
            },],
            css=template_css,
        )

        self.anki_model = grammar_model


    def generate_deck(self) -> None:
        print(f"Generating {self.jlpt_level.capitalize()} {self.LESSON_TYPE} deck...", end='\r')

        deck_id = random.randrange(1 << 30, 1 << 31)
        grammar_deck = genanki.Deck(deck_id, f'JLPT Sensei {self.jlpt_level.upper()} {self.LESSON_TYPE.capitalize()}')

        with open(f'data/{self.LESSON_TYPE}/{self.jlpt_level}_{self.LESSON_TYPE}_list.csv', encoding='utf8') as grammar_csv:
            grammar_csv_reader = csv.reader(grammar_csv, delimiter=',')
            next(grammar_csv_reader) # skip column headings

            for row in grammar_csv_reader:
                g_index, grammar, g_reading, g_meaning, g_source = list(row)
                relative_img_path = f'<img src="flashcard{g_index}.jpg">'
                grammar_note = genanki.Note(
                    model=self.anki_model,
                    fields=[grammar, g_reading, g_meaning, '', '', '', relative_img_path, g_source, g_index]
                )

                grammar_deck.add_note(grammar_note)
        
        self.media_files = [f"data/grammar/flashcard_images/{self.jlpt_level}/flashcard{g_index}.jpg" for g_index in range(1, len(grammar_deck.notes)+1)]
        self.anki_deck = grammar_deck
    

    def main(self):
        self.generate_model()
        self.generate_deck()
        self.save_deck()
