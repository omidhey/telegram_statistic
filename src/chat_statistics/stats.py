import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Union

import arabic_reshaper
from bidi.algorithm import get_display
from hazm import Normalizer, sent_tokenize, word_tokenize
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
        stop_words = set(map(str.strip, stop_words))
        self.stop_words = set(map(self.normalizer.normalize, stop_words))

    @staticmethod
    def rebuild_msg(sub_messages):
        """This function rebuild telegram massege
        """
        msg_text = ''
        for sub_msg in sub_messages:
            if isinstance(sub_msg, str):
                msg_text += sub_msg
            elif 'text' in sub_msg:
                msg_text += sub_msg['text']
        return msg_text

    def message_has_question(self, msg):
        """Checks if a message has a question

        :param msg: message to check
        """
        if not isinstance(msg['text'], str):
            msg['text'] = self.rebuild_msg(msg['text'])

        sentences = sent_tokenize(msg['text'])
        for sentence in sentences:
            if ("?" not in msg['text']) and ("؟" not in msg['text']):
                continue

            return True

    def generate_top_users(self, top_n:int = 10) -> dict:
        """Get the top n users from the chat.

        :param top_n: number of users to get, default to 10
        :return: dict of top users
        """
        # check messages for questions
        is_question = defaultdict(bool)
        for msg in self.chat_data['messages']:
            if not isinstance(msg['text'], str):
                msg['text'] = self.rebuild_msg(msg['text'])

            sentences = sent_tokenize(msg['text'])
            for sentence in sentences:
                if ("?" not in msg['text']) and ("؟" not in msg['text']):
                    continue

                is_question[msg['id']] = True
                break

        # get top users based on replying to quesitons from others
        logger.info("Getting top users...")
        users = []
        for msg in self.chat_data['messages']:
            if not msg.get('reply_to_message_id'):
                continue
            if is_question[msg['reply_to_message_id']] is False:
                continue
            users.append(msg['from'])

        return dict(Counter(users).most_common(top_n))


    def generate_word_cloud(
            self, output_dir: Union[str, Path],
            width: int = 1200, height: int = 600,
            max_font_size: int = 250,
            background_color: str ='white',
            ):
        """
        Generates a word cloud from the chat date

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
            width=width, height=height, margin=2,
            min_font_size=1, max_font_size=max_font_size,
            background_color=background_color,
            ).generate(text_content)

        logger.info(f"Saving word cloud to {output_dir}")
        wordcloud.to_file(str(Path(output_dir) / 'wordcould.png'))


if __name__ == "__main__":
    chat_stats = ChatStatistics(chat_json=str(DATA_DIR / 'online.json'))
    top_users = chat_stats.generate_top_users(top_n=10)
    print(top_users)
    chat_stats.generate_word_cloud(output_dir=str(DATA_DIR))
    print('Done!')