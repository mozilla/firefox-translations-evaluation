import subprocess
import os
from collections import defaultdict
from datetime import datetime
import statistics

from sacrebleu import dataset
import click
from toolz import groupby
from glob import glob
import pandas as pd

HOME_DIR = '/workspace'
BERGAMOT_EVALUATION_DIR = os.path.join(HOME_DIR, 'bergamot-evaluation')
RESULTS_DIR = os.path.join(BERGAMOT_EVALUATION_DIR, 'results')
IMG_DIR = os.path.join(RESULTS_DIR, 'img')

EVAL_PATH = os.path.join(BERGAMOT_EVALUATION_DIR, 'eval', 'eval.sh')

BERGAMOT_MODELS_DIR = os.path.join(HOME_DIR, 'bergamot-models', 'prod')
BERGAMOT_APP_PATH = os.path.join(HOME_DIR, 'bergamot-translator', 'build', 'app', 'bergamot-translator-app')
BERGAMOT_EVAL_PATH = os.path.join(BERGAMOT_EVALUATION_DIR, 'translators', 'bergamot.sh')

MARIAN_APP_PATH = os.path.join(HOME_DIR, 'marian-dev', 'build', 'marian-decoder')
MARIAN_EVAL_PATH = os.path.join(BERGAMOT_EVALUATION_DIR, 'translators', 'marian.sh')

trans_order = {'bergamot': 0,
               'marian': 1,
               'google': 2,
               'microsoft': 3}


def evaluate(pair, set_name, translator):
    source, target = pair

    my_env = os.environ.copy()
    my_env['SRC'] = source
    my_env['TRG'] = target
    my_env['DATASET'] = set_name
    my_env['EVAL_DIR'] = RESULTS_DIR
    my_env['TRANSLATOR'] = translator

    if translator == 'bergamot':
        my_env['MODEL_DIR'] = os.path.join(BERGAMOT_MODELS_DIR, f'{source}{target}')
        my_env['APP_PATH'] = BERGAMOT_APP_PATH
        cmd = f'bash {BERGAMOT_EVAL_PATH}'
    elif translator == 'marian':
        my_env['MODEL_DIR'] = os.path.join(BERGAMOT_MODELS_DIR, f'{source}{target}')
        my_env['APP_PATH'] = MARIAN_APP_PATH
        cmd = f'bash {MARIAN_EVAL_PATH}'
    elif translator == 'google':
        cmd = f"python3 {os.path.join(BERGAMOT_EVALUATION_DIR, 'translators', 'google_translate.py')}"
    elif translator == 'microsoft':
        cmd = f"python3 {os.path.join(BERGAMOT_EVALUATION_DIR, 'translators', 'microsoft.py')}"
    else:
        raise ValueError(f'Translator is not supported: {translator}')

    my_env['TRANSLATOR_CMD'] = cmd
    res = subprocess.run(['bash', EVAL_PATH], env=my_env, stdout=subprocess.PIPE)

    return float(res.stdout.decode('utf-8').strip())


def build_report():
    results = read_results()
    os.makedirs(IMG_DIR, exist_ok=True)

    lines = ['# Evaluation results',
             '\n Evaluation is done using [SacreBLEU](https://github.com/mjpost/sacrebleu) '
             'and official WMT ([Conference on Machine Translation](http://statmt.org/wmt17)) datasets.']

    avg_results = get_avg_scores(results)
    build_section(avg_results, 'avg', lines)

    for lang_pair, datasets in results.items():
        build_section(datasets, lang_pair, lines)

    results_path = os.path.join(RESULTS_DIR, datetime.today().strftime('%Y-%m-%d') + '_results.md')
    with open(results_path, 'w+') as f:
        f.write('\n'.join(lines))
        print(f'Results are written to {results_path}')


def build_section(datasets, key, lines):
    lines.append(f'\n## {key}\n')
    lines.append(f'| Translator/Dataset | {" | ".join(datasets.keys())} |')
    lines.append(f"| {' | '.join(['---' for _ in range(len(datasets) + 1)])} |")

    inverted_formatted = defaultdict(dict)
    inverted_scores = defaultdict(dict)

    for dataset_name, translators in datasets.items():
        bergamot_res = translators.get('bergamot')
        reordered = sorted(translators.items(), key=lambda x: trans_order[x[0]])

        for translator, score in reordered:
            if translator != 'bergamot' and bergamot_res:
                change_perc = (score - bergamot_res) / bergamot_res * 100
                change = score - bergamot_res
                sign = '+' if change > 0 else ''
                formatted_score = f'{score:.2g} ({sign}{change:.1g}, {sign}{change_perc:.2g}%)'
            else:
                formatted_score = f'{score:.2f}'

            inverted_formatted[translator][dataset_name] = formatted_score
            inverted_scores[translator][dataset_name] = score

    for translator, scores in inverted_formatted.items():
        lines.append(f'| {translator} | {" | ".join(scores.values())} |')

    img_path = os.path.join(IMG_DIR, f'{key}.png')
    plot_lang_pair(datasets, inverted_scores, img_path)

    img_relative_path = '/'.join(img_path.split("/")[-2:])
    lines.append(f'\n![Results]({img_relative_path})')


def read_results():
    results = defaultdict(dict)
    for bleu_file in glob(RESULTS_DIR + '/*/*.bleu'):
        dataset_name, translator, = os.path.basename(bleu_file).split('.')[:2]
        pair = bleu_file.split('/')[-2]
        with open(bleu_file) as f:
            score = float(f.read().strip())

        if dataset_name not in results[pair]:
            results[pair][dataset_name] = {}
        results[pair][dataset_name][translator] = score
    return results


def get_avg_scores(results):
    scores = {}
    for lang_pair, datasets in results.items():
        tran_scores = [(tran, score)
                       for data, trans in datasets.items()
                       for tran, score in trans.items()]
        avg_scores = {tran: statistics.mean([s for _, s in scores])
                      for tran, scores in groupby(lambda x: x[0], tran_scores).items()}
        scores[lang_pair] = avg_scores
    return scores


def plot_lang_pair(datasets, inverted_scores, img_path):
    trans_scores = {t: s.values() for t, s in inverted_scores.items()}
    df = pd.DataFrame(trans_scores, index=datasets, columns=trans_order.keys())
    fig = df.plot.bar(ylim=(20, None), ylabel='bleu').get_figure()
    fig.set_size_inches(18.5, 10.5)
    fig.savefig(img_path, bbox_inches="tight")


@click.command()
@click.option('--pairs',
              default='all',
              help='Comma separated language pairs or `all`. Example: es-en,de-et')
@click.option('--translators',
              default='bergamot',
              help='Comma separated translators. Example: bergamot,google')
@click.option('--skip-existing',
              default=False,
              is_flag=True,
              help='Whether to skip already calculated scores. '
                   'They are located in `results/xx-xx` folders as *.bleu files.')
def run(pairs, translators, skip_existing):
    lang_pairs = [(pair[:2], pair[-2:])
                  for pair in (os.listdir(BERGAMOT_MODELS_DIR) if pairs == 'all' else pairs.split(','))]
    print(f'Language pairs to evaluate: {lang_pairs}')

    for pair in lang_pairs:
        formatted_pair = f'{pair[0]}-{pair[1]}'

        for dataset_name, descr in dataset.DATASETS.items():
            # consider only official wmtXX datasets
            if not dataset_name.startswith('wmt') or len(dataset_name) > 5 or formatted_pair not in descr:
                continue

            reordered = sorted(translators.split(','), key=lambda x: trans_order[x])
            for translator in reordered:
                print(f'Evaluation for dataset: {dataset_name}, translator: {translator}, pair: {formatted_pair}')

                res_path = os.path.join(RESULTS_DIR, formatted_pair, f'{dataset_name}.{translator}.{pair[1]}.bleu')
                if skip_existing and os.path.isfile(res_path):
                    with open(res_path) as f:
                        bleu = float(f.read().strip())
                else:
                    bleu = evaluate(pair, dataset_name, translator)

                print(f'Result BLEU: {bleu}\n')

    build_report()


if __name__ == '__main__':
    run()
