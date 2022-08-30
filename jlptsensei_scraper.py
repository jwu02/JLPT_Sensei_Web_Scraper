from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import os
import urllib.parse
from random import randint
# import multiprocessing as mp


JLPT_LEVELS = ['n5', 'n4', 'n3', 'n2', 'n1']
LESSON_TYPES = ['grammar', 'vocabulary']


def scrape_sensei(jlpt_level: str, lesson_type: str):
    """
    Scrape a JLPT level for a particular lesson type
    """
    page_number = 1
    retrieved_thead = False

    while True:
        try:
            # link format: https://jlptsensei.com/jlpt-n5-grammar-list/page/1/
            html = urlopen(f'https://jlptsensei.com/jlpt-{jlpt_level}-{lesson_type}-list/page/{page_number}')
        except HTTPError as e:
            print(e)
            break
        except URLError as e:
            print(e)
            break
        
        print(f"Scraping {jlpt_level.capitalize()} {lesson_type}, page {page_number}...", end="\r")

        bs = BeautifulSoup(html, 'lxml') # 'html.parser' didn't work well

        try:
            # get table element we are interested in
            if lesson_type == 'vocabulary':
                table_element = bs.find('table', {'id': 'jl-vocab'})
            elif lesson_type == 'grammar':
                table_element = bs.find('table', {'id': 'jl-grammar'})

            if not retrieved_thead:
                table_headings = []
                # get table headings
                th_elements = table_element.thead.find_all('th')
                for th in th_elements:
                    table_headings.append(th.string)

                # creating a Pandas dataframe with the fetched headings
                df = pd.DataFrame(columns=table_headings)

                # rename some column headings
                rename_mapping = {}
                if lesson_type == 'vocabulary':
                    rename_mapping = {df.columns[1]: 'Vocabulary', df.columns[2]: 'Reading'}
                elif lesson_type == 'grammar':
                    df = df.drop('Grammar Lesson', axis=1) # drop romji reading column from df
                    rename_mapping = {df.columns[1]: 'Grammar Lesson'}
                df = df.rename(columns=rename_mapping)

                retrieved_thead = True

            # get table rows
            tr_elements = table_element.tbody.find_all('tr', {'class': 'jl-row'})
            # get table data in rows
            for tr in tr_elements:
                row_data = []
                for td_element in tr.find_all('td'):
                    if lesson_type == 'vocabulary' and td_element['class'][0] == 'jl-td-vr':
                        # only want furigana if it exists and not the romaji, from vocabulary table
                        vocab_reading_td = ""
                        try:
                            vocab_reading_td = td_element.a.p.string
                        except AttributeError as e:
                            pass
                        
                        row_data.append(vocab_reading_td)
                    elif lesson_type == 'grammar' and td_element['class'][0] == 'jl-td-gr':
                        # skip the romaji readings from grammar table
                        pass
                    else:
                        row_data.append(td_element.string)

                # insert row data into dataframe
                df.loc[len(df)] = row_data
        except AttributeError as e:
            print("No more table pages...", end="\r")
            break

        # increment variable to scrape next table page
        page_number += 1

    if lesson_type == 'vocabulary':
        df = add_example_sentences(df, jlpt_level)

        # global scraped_sentences
        # scraped_sentences = 0

        # global total_vocab
        # total_vocab = len(df.index)

        # with mp.Pool(2) as pool:
        #     # result = pool.map(add_example_sentence_row, df.iterrows(), chunksize=10)
        #     result = pool.imap(add_example_sentence_row, df.itertuples(name=None), chunksize=10)
        #     # result = [pool.apply(add_example_sentence_row, args=(row, 4, 8)) for row in df]
        #     df = pd.DataFrame(result)

    df_to_csv(df, jlpt_level, lesson_type)

    print(f"Finished scraping {jlpt_level.capitalize()} {lesson_type}.")


def add_example_sentences(df: pd.DataFrame, jlpt_level: str) -> pd.DataFrame:
    """
    Add example sentences for vocabulary lists
    """
    i = -1

    # visit each vocabulary link for examples sentences
    for vocab in df['Vocabulary']:
        i += 1

        print(f"Scraping sentence {i}/{len(df['Vocabulary'])}", end="\r")
        
        try:
            html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/{urllib.parse.quote(vocab)}")
        except HTTPError as e:
            try:
                # some links can't be followed directly with only the vocab
                # need to append "japanese-meaning-of-" before vocab
                html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/japanese-meaning-of-{urllib.parse.quote(vocab)}")
            except HTTPError as e:
                try:
                    html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/jlpt-{jlpt_level}-vocabulary-{urllib.parse.quote(vocab)}")
                except HTTPError as e:
                    try:
                        # replace vocab with its reading with furigana
                        vocab_reading = df.loc[df['Vocabulary'] == vocab]['Reading']
                        html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/{urllib.parse.quote(vocab_reading)}")
                    except HTTPError as e:
                        # dealing with more exceptional cases
                        # where the scraped vocab uses a different form in url
                        if vocab == "晩ご飯":
                            try:
                                html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/{urllib.parse.quote('晩御飯')}")
                            except HTTPError as e:
                                print(f"{e} for #{df.at[i, '#']} {df.at[i, 'Vocabulary']}")
                                continue
                        else:
                            print(f"{e} for #{df.at[i, '#']} {df.at[i, 'Vocabulary']}")
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
            print(f"No example sentences found for #{df.at[i, '#']} {df.at[i, 'Vocabulary']}")
            continue

        # choose a random example sentence to scrape
        rand_example_i = randint(0, len(example_elements)-1)
        jp_sentence_element = example_elements[rand_example_i].find('div', {'class': 'example-main'})
        en_sentence_element = example_elements[rand_example_i].find('div', {'id': f'example_{rand_example_i+1}_en'})

        df.at[i, 'Sentence JP'] = jp_sentence_element.text
        df.at[i, 'Sentence EN'] = en_sentence_element.string

    return df

def add_example_sentence_row(df_row):
    """
    Take advantage of multiprocessing to speed up sentence scraping process
    (doesn't work)
    """

    # print(df_row)
    scraped_sentences += 1
    print(f"Scraped {scraped_sentences}/{total_vocab} sentences", end="\r")

    try:
        html = urlopen(f"https://jlptsensei.com/learn-japanese-vocabulary/{urllib.parse.quote(df_row[2])}")
    except HTTPError as e:
        print(f"{e} for #{df_row[1]} {df_row[2]}")
        return df_row
    except URLError as e:
        print(f"{e} for #{df_row[1]} {df_row[2]}")
        return df_row
    
    bs = BeautifulSoup(str(html), 'lxml')

    try:
        example_elements = bs.find_all('div', {'class': 'example-cont'})
        if len(example_elements) == 0:
            # if no example sentences are found raise exception
            raise AttributeError
    except AttributeError as e:
        print(f"No example sentences found for #{df_row[1]} {df_row[2]}")
        return df_row

    # choose a random example sentence to scrape
    rand_example_i = randint(0, len(example_elements)-1)
    jp_sentence_element = example_elements[rand_example_i].find('div', {'class': 'example-main'})
    en_sentence_element = example_elements[rand_example_i].find('div', {'id': f'example_{rand_example_i+1}_en'})

    new_df_row = list(df_row)
    new_df_row.append(jp_sentence_element.text)
    new_df_row.append(en_sentence_element.string)

    return new_df_row


def df_to_csv(df: pd.DataFrame, jlpt_level: str, lesson_type: str):
    """
    Save dataframe as csv file
    """
    outdir = f'./data/{lesson_type}'
    dir_exists(outdir)

    outname = f"{jlpt_level}_{lesson_type}_list.csv"
    fullname = os.path.join(outdir, outname)

    # convert df into a csv file
    df.to_csv(fullname, index=False)


def dir_exists(dirname: str):
    """
    Check if a dirctory exists, if not it will be created
    """
    if not os.path.exists(dirname):
        os.mkdir(dirname)


if __name__ == "__main__":
    JLPT_LEVELS = ['n5']

    for level in JLPT_LEVELS:
        # scrape_sensei(level, 'grammar')
        scrape_sensei(level, 'vocabulary')

    # INCOMPLETE_LEVELS = ['n2', 'n1']
    # for level in INCOMPLETE_LEVELS:
    #     scrape_sensei(level, 'vocabulary')
    
    print("JLPT Sensei scraping complete.")
