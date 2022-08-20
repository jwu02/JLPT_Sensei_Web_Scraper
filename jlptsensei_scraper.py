from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
import pandas as pd
import os


JLPT_LEVELS = ['n5', 'n4', 'n3', 'n2', 'n1']
LESSON_TYPES = ['grammar', 'vocabulary']


def scrape_sensei(jlpt_level, lesson_type):
    """
    Scrape a JLPT level for a particular lesson type
    """

    page_number = 1
    retrieved_thead = False

    while True:

        try:
            # https://jlptsensei.com/jlpt-n5-grammar-list/page/1/
            html = urlopen(f'https://jlptsensei.com/jlpt-{jlpt_level}-{lesson_type}-list/page/{page_number}')
        except HTTPError as e:
            print(e)
            break
        except URLError as e:
            print(e)
            break
        
        print(f"Scraping {jlpt_level.capitalize()} {lesson_type}, page {page_number}...", end="\r")

        # 'html.parser' didn't work well
        bs = BeautifulSoup(html, 'lxml')

        try:
            # get table element we are interested in
            if lesson_type == 'vocabulary':
                table_element = bs.find('table', {'id':f'jl-vocab'})
            else:
                table_element = bs.find('table', {'id':f'jl-{lesson_type}'})

            if not retrieved_thead:
                # get table headings
                table_headings = []
                th_elements = table_element.thead.find_all('th')
                for th in th_elements:
                    table_headings.append(th.string)

                # creating a Pandas dataframe with the fetched headings
                df = pd.DataFrame(columns=table_headings)
                retrieved_thead = True

                # rename some column headings
                rename_mapping = {}
                if lesson_type == 'vocabulary':
                    rename_mapping = {df.columns[1]: 'Vocabulary', df.columns[2]: 'Reading'}
                elif lesson_type == 'grammar':
                    rename_mapping = {df.columns[1]: 'GrammarRomaji', df.columns[2]: 'GrammarKanji'}
                df = df.rename(columns=rename_mapping)

            # get table rows
            tr_elements = table_element.tbody.find_all('tr', {'class':'jl-row'})
            # get table data in rows
            for tr in tr_elements:
                row_data = []
                for td_element in tr.find_all('td'):
                    if td_element['class'][0] == 'jl-td-vr':
                        # special case for third column when scraping vocabulary table
                        special_td = ""
                        try:
                            special_td = td_element.a.p.string
                        except AttributeError as e:
                            pass
                        
                        row_data.append(special_td)
                    else:
                        row_data.append(td_element.string)

                # insert row data into dataframe
                df.loc[len(df)] = row_data
        except AttributeError as e:
            print("No more table pages...", end="\r")
            break

        # increment variable to scrape next table page
        page_number += 1

    outname = f"{jlpt_level}_{lesson_type}_list.csv"
    df_to_csv(df, outname)

    print(f"Finished scraping {jlpt_level.capitalize()} {lesson_type}.")


def df_to_csv(df, outname):
    """
    Create data directory if doesn't already, and save df as csv
    """

    outdir = './data'
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    fullname = os.path.join(outdir, outname)    

    # convert df into a csv file to convert into Anki flashcards
    df.to_csv(fullname, index=False)


if __name__ == "__main__":
    for lv in JLPT_LEVELS:
        for lt in LESSON_TYPES:
            scrape_sensei(lv, lt)

    # scrape_sensei('n1', 'vocabulary')
    # scrape_sensei('n2', 'vocabulary')
    
    print("JLPT Sensei scraping complete.")
