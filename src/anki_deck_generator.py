from abc import ABC, abstractmethod
import genanki
from pathlib import Path
import os


class AnkiDeckGenerator(ABC):
    def __init__(self, level: str) -> None:
        self.jlpt_level = level
        self.anki_model = genanki.Model()
        self.anki_deck = genanki.Deck()

        self.LESSON_TYPE = ''


    @abstractmethod
    def generate_model(self) -> None:
        """
        Return a model which defines the fields and cards for a type of note
        """
        pass


    @abstractmethod
    def generate_deck(self) -> None:
        """
        Read CSV file and convert each row into an Anki card
        """
        pass


    def save_deck(self) -> None:
        outdir = './data/decks'
        Path(outdir).mkdir(parents=True, exist_ok=True)

        filename = f'JLPT_Sensei_{self.jlpt_level.capitalize()}_{self.LESSON_TYPE.capitalize()}.apkg'
        fullpath = os.path.join(outdir, filename)
        genanki.Package(self.anki_deck).write_to_file(fullpath)

        print(f"Finished generating {self.jlpt_level.capitalize()} {self.LESSON_TYPE.capitalize()} Deck!")
