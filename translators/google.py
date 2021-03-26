# Pricing
# https://cloud.google.com/translate/pricing

import os

from google.cloud import translate_v2 as translate
import sys

translate_client = translate.Client()


def translate(texts):
    """Translates text into the target language.

    Texts must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """
    source = os.environ['SRC']
    target = os.environ['TRG']

    results = translate_client.translate(texts, target_language=target, source_language=source)
    return [r['translatedText'] for r in results]


if __name__ == '__main__':
    texts = [line.strip() for line in sys.stdin]
    tranlations = translate(texts)
    sys.stdout.write('\n'.join(tranlations))
