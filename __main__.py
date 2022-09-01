from vocabulary_scraper import VocabularyScraper
from grammar_scraper import GrammarScraper

from vocabulary_deck_generator import VocabularyDeckGenerator
from grammar_deck_generator import GrammarDeckGenerator


def scraper():
    LEVELS_TO_SCRAP = [
        # 'n5',
        # 'n4',
        # 'n3',
        # 'n2',
        'n1'
    ]

    for level in LEVELS_TO_SCRAP:
        VocabularyScraper(level).scrape()
        GrammarScraper(level).scrape()

    print("JLPT Sensei scraping complete.")


def deck_generator():
    LEVELS_TO_GENERATE = [
        'n5',
        'n4',
        # 'n3',
        # 'n2',
        # 'n1'
    ]

    for level in LEVELS_TO_GENERATE:
        VocabularyDeckGenerator(level).main()
    
    print("Finished generating anki decks.")


if __name__ == '__main__':
    # scraper()
    deck_generator()
