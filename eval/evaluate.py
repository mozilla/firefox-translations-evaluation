import subprocess
import os
from collections import defaultdict
from datetime import datetime
import statistics

from sacrebleu import dataset
import click
from toolz import groupby

HOME_DIR = '/workspace'
BERGAMOT_EVALUATION_DIR = os.path.join(HOME_DIR, 'bergamot-evaluation')
RESULTS_DIR = os.path.join(BERGAMOT_EVALUATION_DIR, 'results')

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
        cmd = f"python3 {os.path.join(BERGAMOT_EVALUATION_DIR, 'translators', 'google.py')}"
    elif translator == 'microsoft':
        cmd = f"python3 {os.path.join(BERGAMOT_EVALUATION_DIR, 'translators', 'microsoft.py')}"
    else:
        raise ValueError(f'Translator is not supported: {translator}')

    my_env['TRANSLATOR_CMD'] = cmd
    # print(f'Running evaluation with env:\n{my_env}\ncmd: {cmd}')
    res = subprocess.run(['bash', EVAL_PATH], env=my_env, stdout=subprocess.PIPE)

    return float(res.stdout.decode('utf-8').strip())


def save_results(results):
    lines = ['# Evaluation results']

    for lang_pair, datasets in results.items():
        # add average score on all datasets
        tran_scores = [(tran, score) for data, trans in datasets.items() for tran, score in trans.items()]
        datasets['avg'] = {tran: statistics.mean([s for _, s in scores])
                           for tran, scores in groupby(lambda x: x[0], tran_scores).items()}

        lines.append(f'\n## {lang_pair}\n')
        lines.append(f'| Translator/Dataset | {" | ".join(datasets.keys())} |')
        lines.append(f"| {' | '.join(['---' for _ in range(len(datasets) + 1)])} |")
        inverted = defaultdict(dict)

        for dataset_name, translators in datasets.items():
            bergamot_res = translators.get('bergamot')

            for translator, score in translators.items():
                if translator != 'bergamot' and bergamot_res:
                    change = (score - bergamot_res) / score * 100
                    sign = '+' if change > 0 else ''
                    formatted_score = f'{score:.2f} ({sign}{change:.2f}%)'
                else:
                    formatted_score = f'{score:.2f}'
                inverted[translator][dataset_name] = formatted_score

        for translator, scores in inverted.items():
            lines.append(f'| {translator} | {" | ".join(scores.values())} |')

    results_path = os.path.join(RESULTS_DIR, datetime.today().strftime('%Y-%m-%d') + '_results.md')
    with open(results_path, 'w+') as f:
        f.write('\n'.join(lines))

    print(f'Results are written to {results_path}')


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
    results = {}
    print(lang_pairs)

    for pair in lang_pairs:
        formatted_pair = f'{pair[0]}-{pair[1]}'
        results[formatted_pair] = {}

        for dataset_name, descr in dataset.DATASETS.items():
            # consider only official wmtXX datasets
            if not dataset_name.startswith('wmt') or len(dataset_name) > 5 or formatted_pair not in descr:
                continue

            results[formatted_pair][dataset_name] = {}

            for translator in translators.split(','):
                print(f'Evaluation for dataset: {dataset_name}, translator: {translator}, pair: {formatted_pair}')

                res_path = os.path.join(RESULTS_DIR, formatted_pair, f'{dataset_name}.{translator}.{pair[1]}.bleu')
                if skip_existing and os.path.isfile(res_path):
                    with open(res_path) as f:
                        bleu = float(f.read().strip())
                else:
                    bleu = evaluate(pair, dataset_name, translator)

                print(f'Result BLEU: {bleu}\n')
                results[formatted_pair][dataset_name][translator] = bleu

    save_results(results)


if __name__ == '__main__':
    run()
