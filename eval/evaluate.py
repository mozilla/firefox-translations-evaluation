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
BERGAMOT_APP_DIR = os.path.join(HOME_DIR, 'bergamot-translator', 'build', 'app')
BERGAMOT_PATH = os.path.join(BERGAMOT_EVALUATION_DIR, 'translators', 'bergamot.sh')

MARIAN_APP_DIR = os.path.join(HOME_DIR, 'marian-dev', 'build')
MARIAN_PATH = os.path.join(BERGAMOT_EVALUATION_DIR, 'translators', 'marian.sh')


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
        my_env['BERGAMOT_APP_DIR'] = BERGAMOT_APP_DIR
        cmd = f'bash {BERGAMOT_PATH}'
    elif translator == 'marian':
        my_env['MODEL_DIR'] = os.path.join(BERGAMOT_MODELS_DIR, f'{source}{target}')
        my_env['MARIAN_APP_DIR'] = MARIAN_APP_DIR
        cmd = f'bash {MARIAN_PATH}'
    elif translator == 'google':
        cmd = f"python3 {os.path.join(BERGAMOT_EVALUATION_DIR, 'translators', 'google_translate.py')}"
    elif translator == 'microsoft':
        cmd = f"python3 {os.path.join(BERGAMOT_EVALUATION_DIR, 'translators', 'microsoft.py')}"
    else:
        raise ValueError(f'Translator is not supported: {translator}')

    my_env['TRANSLATOR_CMD'] = cmd
    # print(f'Running evaluation with env:\n{my_env}\ncmd: {cmd}')
    res = subprocess.run(['bash', EVAL_PATH], env=my_env, stdout=subprocess.PIPE)

    return float(res.stdout.decode('utf-8').strip())


def build_report():
    results = read_results()
    add_avg_scores(results)
    os.makedirs(IMG_DIR, exist_ok=True)

    lines = ['# Evaluation results']
    all_img_path = os.path.join(IMG_DIR, f'all.png')
    plot_avg_scores(results, all_img_path)
    lines.append(f'\n![All results]({img_relative_path(all_img_path)})')

    for lang_pair, datasets in results.items():
        lines.append(f'\n## {lang_pair}\n')
        lines.append(f'| Translator/Dataset | {" | ".join(datasets.keys())} |')
        lines.append(f"| {' | '.join(['---' for _ in range(len(datasets) + 1)])} |")
        inverted_formatted = defaultdict(dict)
        inverted_scores = defaultdict(dict)

        for dataset_name, translators in datasets.items():
            bergamot_res = translators.get('bergamot')

            for translator, score in translators.items():
                if translator != 'bergamot' and bergamot_res:
                    change = (score - bergamot_res) / bergamot_res * 100
                    sign = '+' if change > 0 else ''
                    formatted_score = f'{score:.2f} ({sign}{change:.2f}%)'
                else:
                    formatted_score = f'{score:.2f}'
                inverted_formatted[translator][dataset_name] = formatted_score
                inverted_scores[translator][dataset_name] = score

        for translator, scores in inverted_formatted.items():
            lines.append(f'| {translator} | {" | ".join(scores.values())} |')

        img_path = os.path.join(IMG_DIR, f'{lang_pair}.png')
        plot_lang_pair(datasets, inverted_scores, img_path)
        lines.append(f'\n![Results]({img_relative_path(img_path)})')

    results_path = os.path.join(RESULTS_DIR, datetime.today().strftime('%Y-%m-%d') + '_results.md')
    with open(results_path, 'w+') as f:
        f.write('\n'.join(lines))
        print(f'Results are written to {results_path}')


def img_relative_path(img_path):
    return '/'.join(img_path.split("/")[-2:])


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


def add_avg_scores(results):
    for lang_pair, datasets in results.items():
        tran_scores = [(tran, score)
                       for data, trans in datasets.items()
                       for tran, score in trans.items()]
        avg_scores = {tran: statistics.mean([s for _, s in scores])
                      for tran, scores in groupby(lambda x: x[0], tran_scores).items()}
        datasets['avg'] = avg_scores


def plot_lang_pair(datasets, inverted_scores, img_path):
    df = pd.DataFrame({t: s.values() for t, s in inverted_scores.items()}, index=datasets.keys())
    plot(df, img_path)


def plot_avg_scores(results, img_path):
    avg_scores = [(tran, score) for datasets in results.values()
                  for tran, score in datasets['avg'].items()]
    groups = {key: [s for t, s in scores]
              for key, scores in groupby(lambda x: x[0], avg_scores).items()}
    df = pd.DataFrame(groups, index=results.keys())
    plot(df, img_path)


def plot(df, img_path):
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

            for translator in translators.split(','):
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
