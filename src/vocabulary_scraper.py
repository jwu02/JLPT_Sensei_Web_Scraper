from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import urllib.parse
from random import randint
from src.jlptsensei_scraper import JLPTSenseiScraper
# import multiprocessing as mp


class VocabularyScraper(JLPTSenseiScraper):
    def __init__(self, level: str) -> None:
        super().__init__(level)

        self.LESSON_TYPE = 'vocabulary'

        column_names = ['#', 'Vocabulary', 'Reading', 'Type', 'Meaning', 'Sentence JP', 'Sentence EN']
        self.scraped_df = pd.DataFrame(columns=column_names)


    def scrape(self):
        page_number = 1

        while True:
            try:
                html = urlopen(f'https://jlptsensei.com/jlpt-{self.jlpt_level}-vocabulary-list/page/{page_number}')
            except HTTPError as e:
                print(e)
                break
            except URLError as e:
                print(e)
                break
            
            print(f"Scraping {self.jlpt_level.capitalize()} {self.LESSON_TYPE}, page {page_number}...", end="\r")

            bs = BeautifulSoup(html, 'lxml') # 'html.parser' didn't work well

            try:
                # get table element we are interested in
                table_element = bs.find('table', {'id': 'jl-vocab'})

                # get table rows
                tr_elements = table_element.tbody.find_all('tr', {'class': 'jl-row'})
                # get table data in rows
                for tr in tr_elements:
                    row_data = []
                    for td_element in tr.find_all('td'):
                        if td_element['class'][0] == 'jl-td-vr':
                            # only want furigana if it exists and not the romaji, from vocabulary table
                            vocab_reading_td = ""
                            try:
                                vocab_reading_td = td_element.a.p.string
                            except AttributeError as e:
                                pass
                            
                            row_data.append(vocab_reading_td)
                        else:
                            row_data.append(td_element.string)

                    # insert row data into dataframe
                    self.scraped_df.loc[len(self.scraped_df)] = row_data
            except AttributeError as e:
                print("No more table pages...", end="\r")
                break

            # increment variable to scrape next table page
            page_number += 1
        
        print(f"Finished scraping {self.jlpt_level.capitalize()} vocabulary tables.")

        self.scraped_df = self.scrape_sentences()
        print(f"Finished scraping {self.jlpt_level.capitalize()} vocabulary sentences.")

        # global scraped_sentences
        # scraped_sentences = 0

        # global total_vocab
        # total_vocab = len(df.index)

        # with mp.Pool(2) as pool:
        #     # result = pool.map(add_example_sentence_row, df.iterrows(), chunksize=10)
        #     result = pool.imap(add_example_sentence_row, df.itertuples(name=None), chunksize=10)
        #     # result = [pool.apply(add_example_sentence_row, args=(row, 4, 8)) for row in df]
        #     df = pd.DataFrame(result)

        self.df_to_csv()


    def scrape_sentences(self) -> pd.DataFrame:
        """
        Add example sentences for vocabulary lists
        """
        i = -1

        # visit each vocabulary link for examples sentences
        for vocab in self.scraped_df['Vocabulary']:
            i += 1

            print(f"Scraping sentence {i}/{len(self.scraped_df.index)}", end="\r")
            
            try:
                html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/{urllib.parse.quote(vocab)}")
            except HTTPError as e:
                try:
                    # some links can't be followed directly with only the vocab
                    # need to append "japanese-meaning-of-" before vocab
                    html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/japanese-meaning-of-{urllib.parse.quote(vocab)}")
                except HTTPError as e:
                    try:
                        html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/jlpt-{self.jlpt_level}-vocabulary-{urllib.parse.quote(vocab)}")
                    except HTTPError as e:
                        try:
                            # replace vocab with its reading with furigana
                            vocab_reading = self.scraped_df.loc[self.scraped_df['Vocabulary'] == vocab]['Reading']
                            html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/{urllib.parse.quote(vocab_reading)}")
                        except HTTPError as e:
                            # dealing with more exceptional cases
                            # where the scraped vocab uses a different form in url
                            if vocab == "晩ご飯":
                                try:
                                    html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/{urllib.parse.quote('晩御飯')}")
                                except HTTPError as e:
                                    print(f"{e} for #{self.scraped_df.at[i, '#']} {self.scraped_df.at[i, 'Vocabulary']}")
                                    continue
                            else:
                                print(f"{e} for #{self.scraped_df.at[i, '#']} {self.scraped_df.at[i, 'Vocabulary']}")
                                continue
            except URLError as e:
                print(e)
                continue
        
            bs = BeautifulSoup(html, 'lxml')

            try:
                example_elements = bs.find_all('div', {'class': 'example-cont'})
                if len(example_elements) == 0:
                    # if no example sentences are found, then move on
                    raise AttributeError

            except AttributeError as e:
                print(f"No example sentences found for #{self.scraped_df.at[i, '#']} {self.scraped_df.at[i, 'Vocabulary']}")
                continue

            # choose a random example sentence to scrape
            rand_example_i = randint(0, len(example_elements)-1)
            jp_sentence_element = example_elements[rand_example_i].find('div', {'class': 'example-main'})
            en_sentence_element = example_elements[rand_example_i].find('div', {'id': f'example_{rand_example_i+1}_en'})

            self.scraped_df.at[i, 'Sentence JP'] = jp_sentence_element.text
            self.scraped_df.at[i, 'Sentence EN'] = en_sentence_element.string

        return self.scraped_df

    # def add_example_sentence_row(self, df_row):
    #     """
    #     Take advantage of multiprocessing to speed up sentence scraping process
    #     (doesn't work)
    #     """

    #     # print(df_row)
    #     scraped_sentences += 1
    #     print(f"Scraped {scraped_sentences}/{total_vocab} sentences", end="\r")

    #     try:
    #         html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/{urllib.parse.quote(df_row[2])}")
    #     except HTTPError as e:
    #         print(f"{e} for #{df_row[1]} {df_row[2]}")
    #         return df_row
    #     except URLError as e:
    #         print(f"{e} for #{df_row[1]} {df_row[2]}")
    #         return df_row
        
    #     bs = BeautifulSoup(str(html), 'lxml')

    #     try:
    #         example_elements = bs.find_all('div', {'class': 'example-cont'})
    #         if len(example_elements) == 0:
    #             # if no example sentences are found raise exception
    #             raise AttributeError
    #     except AttributeError as e:
    #         print(f"No example sentences found for #{df_row[1]} {df_row[2]}")
    #         return df_row

    #     # choose a random example sentence to scrape
    #     rand_example_i = randint(0, len(example_elements)-1)
    #     jp_sentence_element = example_elements[rand_example_i].find('div', {'class': 'example-main'})
    #     en_sentence_element = example_elements[rand_example_i].find('div', {'id': f'example_{rand_example_i+1}_en'})

    #     new_df_row = list(df_row)
    #     new_df_row.append(jp_sentence_element.text)
    #     new_df_row.append(en_sentence_element.string)

    #     return new_df_row
