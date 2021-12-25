import json
from pathlib import Path
from typing import Union

import arabic_reshaper
from bidi.algorithm import get_display
from hazm import Normalizer, word_tokenize
from loguru import logger
from src.data import DATA_DIR
from wordcloud import WordCloud


class ChatStatistics:
    """Generataes chat statistics from a telehram chat json file
    """
    def __init__(self, chat_json: Union[str, Path]):
        """
        :param chat_json:  path to telegram export json file
        """
        # Load chata_data
        logger.info(f"Loading chat data from {chat_json}")
        with open(chat_json) as f:
            self.chat_data = json.load(f)

        self.normalizer = Normalizer()

        # # Load stop_words
        logger.info(f"Loading stopwords from {DATA_DIR / 'stop_words.txt'}")
        # with open (str(DATA_DIR / 'stop_words.txt')) as sws:
        #     stop_words = sws.read().split('\n')
        #     self.stop_words = list(map(self.normalizer.normalize, stop_words)

        stop_words = open(str(DATA_DIR / 'stop_words.txt')).readlines()
        stop_words = list(map(str.strip, stop_words))
        self.stop_words = list(map(self.normalizer.normalize, stop_words))

    def generate_word_cloud(
            self, output_dir: Union[str, Path],
            width: int = 800, height: int = 600,
            max_font_size: int = 250,
            background_color: str ='white',
            ):

        """Generates a word cloud from the chat date

        :param output_dir: path to output directory for word cloud image
        :type output_dir: Union[str, Path]
        """
        logger.info("Loading text content ... ")
        text_content = ''

        for msg in self.chat_data['messages']:
            if type(msg['text']) is str:
                tokens = word_tokenize(msg['text'])
                tokens = list(filter(
                    lambda item: item not in self.stop_words, tokens))
                text_content += f" {' '.join(tokens)}"

        # normalize, reshape for final word cloud

        text_content = self.normalizer.normalize(text_content)
        text_content = arabic_reshaper.reshape(text_content)
        text_content = get_display(text_content)

        # generate word cloud

        logger.info("Generating word cloud ...")
        wordcloud = WordCloud(
            font_path=str(DATA_DIR/'B Homa_0.ttf'),
            width=1200, height=1200, margin=2,
            min_font_size=1, background_color='white',
            ).generate(text_content)

        logger.info(f"Saving word cloud to {output_dir}")
        wordcloud.to_file(str(Path(output_dir) / 'wordcould.png'))


if __name__ == "__main__":
    chat_stats = ChatStatistics(chat_json=str(DATA_DIR / 'online.json'))
    chat_stats.generate_word_cloud(output_dir=str(DATA_DIR))

    print('Done!')
