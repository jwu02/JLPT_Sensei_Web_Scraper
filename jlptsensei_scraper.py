from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import os
from random import randint


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
                
                table_headings.append('Source')

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
                        # only want hiragana readings if it exists and not the romaji, from vocabulary table
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

                # append grammar lesson source link for more details
                row_data.append(tr.find('a', href=True)['href'])

                # insert row data into dataframe
                df.loc[len(df)] = row_data
        except AttributeError as e:
            print("No more table pages...", end="\r")
            break

        # increment variable to scrape next table page
        page_number += 1

    if lesson_type == 'vocabulary':
        df = add_example_sentences(df)

    df_to_csv(df, jlpt_level, lesson_type)

    print(f"Finished scraping {jlpt_level.capitalize()} {lesson_type}.")


def add_example_sentences(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add example sentences for vocabulary lists
    """
    i = 0

    # visit each vocabulary link for examples sentences
    for link in df['Source']:
        print(f"Scraping sentence {i}/{len(df['Source'])}", end="\r")

        try:
            html = urlopen(link)
        except HTTPError as e:
            print(e)
        except URLError as e:
            print(e)
    
        bs = BeautifulSoup(html, 'lxml')

        try:
            example_elements = bs.find_all('div', {'class': 'example-cont'})
            if len(example_elements) == 0:
                # if no example sentences are found, then move on
                raise AttributeError

        except AttributeError as e:
            print(f"No example sentences found for #{df.at[i, '#']} {df.at[i, 'Vocabulary']}")
            i += 1
            continue

        # choose a random example sentence to scrape
        rand_example_i = randint(0, len(example_elements)-1)
        jp_sentence_element = example_elements[rand_example_i].find('div', {'class': 'example-main'})
        en_sentence_element = example_elements[rand_example_i].find('div', {'id': f'example_{rand_example_i+1}_en'})

        df.at[i, 'Sentence JP'] = jp_sentence_element.text
        df.at[i, 'Sentence EN'] = en_sentence_element.string

        i += 1
    
    df = df[['#','Vocabulary', 'Reading', 'Type', 'Meaning', 'Sentence JP', 'Sentence EN', 'Source']]

    return df


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
    for level in JLPT_LEVELS:
        # scrape_sensei(level, 'grammar')
        scrape_sensei(level, 'vocabulary')

    # INCOMPLETE_LEVELS = ['n2', 'n1']
    # for level in INCOMPLETE_LEVELS:
    #     scrape_sensei(level, 'vocabulary')
    
    print("JLPT Sensei scraping complete.")
