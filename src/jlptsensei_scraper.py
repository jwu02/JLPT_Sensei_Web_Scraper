from abc import ABC, abstractmethod
import os
from pathlib import Path
import pandas as pd


class JLPTSenseiScraper(ABC):
    def __init__(self, level: str) -> None:
        self.jlpt_level = level

        self.scraped_df = pd.DataFrame()
        self.LESSON_TYPE = ''
    

    @abstractmethod
    def scrape(self) -> None:
        """
        Scrape a JLPT level for a particular lesson type
        """
        pass


    def df_to_csv(self) -> None:
        """
        Save scraped data into a csv file
        """
        outdir = f'./data/{self.LESSON_TYPE}'
        Path(outdir).mkdir(parents=True, exist_ok=True)

        outname = f'{self.jlpt_level}_{self.LESSON_TYPE}_list.csv'
        fullname = os.path.join(outdir, outname)

        # convert df into a csv file
        self.scraped_df.to_csv(fullname, index=False)

        print(f"Saved {self.jlpt_level.capitalize()} {self.LESSON_TYPE} list.")
