import shutil
import subprocess
import os
from collections import defaultdict
import statistics

from sacrebleu import dataset
import click
from toolz import groupby
from glob import glob
import pandas as pd
from mtdata import iso

HOME_DIR = '/workspace'
EVAL_DIR = os.path.join(HOME_DIR, 'eval')
EVAL_PATH = os.path.join(EVAL_DIR, 'eval.sh')
EVAL_CUSTOM_PATH = os.path.join(EVAL_DIR, 'eval-custom.sh')
CLEAN_CACHE_PATH = os.path.join(EVAL_DIR, 'clean-cache.sh')

CUSTOM_DATASETS = ['flores-dev', 'flores-test']
CUSTOM_DATA_DIR = os.path.join(HOME_DIR, 'data')
FLORES_PATH = os.path.join(CUSTOM_DATA_DIR, 'flores.sh')

BERGAMOT_APP_PATH = os.path.join(HOME_DIR, 'bergamot-translator', 'build', 'app', 'bergamot')
BERGAMOT_EVAL_PATH = os.path.join(HOME_DIR, 'translators', 'bergamot.sh')


TRANS_ORDER = {'bergamot': 0,
               'google': 1,
               'microsoft': 2}


def get_dataset_prefix(dataset_name, pair, results_dir):
    dataset_name = dataset_name.replace('/', '_')
    return os.path.join(results_dir, f'{pair[0]}-{pair[1]}', f'{dataset_name}')


def get_bleu_path(dataset_name, pair, results_dir, translator):
    prefix = get_dataset_prefix(dataset_name, pair, results_dir)
    return f'{prefix}.{translator}.{pair[1]}.bleu'


# Custom data


def download_custom_data():
    print('Downloading Flores dataset')
    os.makedirs(CUSTOM_DATA_DIR, exist_ok=True)
    subprocess.run(['bash', FLORES_PATH, CUSTOM_DATA_DIR])


def copy_flores_lang(dataset_name, lang, eval_prefix):
    flores_dataset = 'dev' if dataset_name == 'flores-dev' else 'devtest'

    if lang == 'zh' or lang == 'zh-Hans':
        lang_code = 'zho_simpl'
    elif lang == 'zh-Hant':
        lang_code = 'zho_trad'
    elif lang == 'nb':
        lang_code = 'nob'
    else:
        lang_code = iso.iso3_code(lang)

    os.makedirs(os.path.dirname(eval_prefix), exist_ok=True)
    shutil.copy(os.path.join(CUSTOM_DATA_DIR, 'flores101_dataset', flores_dataset, f'{lang_code}.{flores_dataset}'),
                f'{eval_prefix}.{lang}')


def copy_custom_data(dataset_name, pair, results_dir):
    src, trg = pair
    eval_prefix = get_dataset_prefix(dataset_name, pair, results_dir)

    if dataset_name.startswith('flores'):
        copy_flores_lang(dataset_name, src, eval_prefix)
        copy_flores_lang(dataset_name, trg, eval_prefix)
    else:
        raise ValueError(f'Unsupported custom dataset: {dataset_name}')


# Evaluation

def find_datasets(pair):
    formatted_pair = f'{pair[0]}-{pair[1]}'
    datasets = []
    datasets += CUSTOM_DATASETS

    for dataset_name, descr in dataset.DATASETS.items():
        is_wmt_official = dataset_name.startswith('wmt') and len(dataset_name) == 5
        is_other_accepted = dataset_name == 'iwslt17' or dataset_name == 'mtedx/test'

        if not (is_wmt_official or is_other_accepted) or formatted_pair not in descr:
            continue

        datasets.append(dataset_name)

    return datasets


def evaluate(pair, set_name, translator, models_dir, results_dir):
    source, target = pair

    my_env = os.environ.copy()
    my_env['SRC'] = source
    my_env['TRG'] = target
    my_env['DATASET'] = set_name
    my_env['EVAL_PREFIX'] = get_dataset_prefix(set_name, pair, results_dir)
    my_env['TRANSLATOR'] = translator

    if translator == 'bergamot':
        my_env['MODEL_DIR'] = os.path.join(models_dir, f'{source}{target}')
        my_env['APP_PATH'] = BERGAMOT_APP_PATH
        cmd = f'bash {BERGAMOT_EVAL_PATH}'
    elif translator == 'google':
        cmd = f"python3 {os.path.join(HOME_DIR, 'translators', 'google_translate.py')}"
    elif translator == 'microsoft':
        cmd = f"python3 {os.path.join(HOME_DIR, 'translators', 'microsoft.py')}"
    else:
        raise ValueError(f'Translator is not supported: {translator}')

    my_env['TRANSLATOR_CMD'] = cmd
    eval_path = EVAL_CUSTOM_PATH if set_name in CUSTOM_DATASETS else EVAL_PATH

    retries = 3
    while True:
        try:
            res = subprocess.run(['bash', eval_path], env=my_env, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            print("stdout: ", res.stdout.decode('utf-8'))
            print("stderr: ", res.stderr.decode('utf-8'))
            float_res = float(res.stdout.decode('utf-8').strip())
            return float_res
        except:
            if retries == 0:
                raise
            retries -= 1
            subprocess.run(['bash', CLEAN_CACHE_PATH])
            print('Attempt failed, retrying')


def run_dir(lang_pairs, skip_existing, translators, results_dir, models_dir):
    reordered = sorted(translators.split(','), key=lambda x: TRANS_ORDER[x])

    for pair in lang_pairs:
        if 'nn' in pair:
            print('There are no evaluation datasets for Norwegian Nynorsk '
                  'and it is not supported by Google and Microsoft API. Skipping evaluation')
            continue

        for dataset_name in find_datasets(pair):
            for translator in reordered:
                print(f'Evaluation for dataset: {dataset_name}, translator: {translator}, pair: {pair[0]}-{pair[1]}')

                res_path = get_bleu_path(dataset_name, pair, results_dir, translator)
                print(f'Searching for {res_path}')

                if skip_existing and os.path.isfile(res_path) and os.stat(res_path).st_size > 0:
                    print(f"Already exists, skipping ({res_path})")
                    with open(res_path) as f:
                        bleu = float(f.read().strip())
                else:
                    print('Not found, running evaluation...')
                    if dataset_name in CUSTOM_DATASETS:
                        copy_custom_data(dataset_name, pair, results_dir)
                    bleu = evaluate(pair, dataset_name, translator, results_dir=results_dir, models_dir=models_dir)

                print(f'Result BLEU: {bleu}\n')


# Report generation

def build_report(res_dir):
    results = read_results(res_dir)
    os.makedirs(os.path.join(res_dir, 'img'), exist_ok=True)

    with open(os.path.join(EVAL_DIR, 'results.md')) as f:
        lines = [l.strip() for l in f.readlines()]

    avg_results = get_avg_scores(results)
    build_section(avg_results, 'avg', lines, res_dir)

    for lang_pair, datasets in results.items():
        build_section(datasets, lang_pair, lines, res_dir)

    results_path = os.path.join(res_dir, 'results.md')
    with open(results_path, 'w+') as f:
        f.write('\n'.join(lines))
        print(f'Results are written to {results_path}')


def build_section(datasets, key, lines, res_dir):
    lines.append(f'\n## {key}\n')
    lines.append(f'| Translator/Dataset | {" | ".join(datasets.keys())} |')
    lines.append(f"| {' | '.join(['---' for _ in range(len(datasets) + 1)])} |")

    inverted_formatted = defaultdict(dict)
    inverted_scores = defaultdict(dict)

    for dataset_name, translators in datasets.items():
        bergamot_res = translators.get('bergamot')
        reordered = sorted(translators.items(), key=lambda x: TRANS_ORDER[x[0]])

        for translator, score in reordered:
            if score == 0:
                formatted_score = 'N/A'
            elif translator != 'bergamot' and bergamot_res:
                change_perc = (score - bergamot_res) / bergamot_res * 100
                change = score - bergamot_res
                sign = '+' if change > 0 else ''
                formatted_score = f'{score:.2f} ({sign}{change:.2f}, {sign}{change_perc:.2f}%)'
            else:
                formatted_score = f'{score:.2f}'

            inverted_formatted[translator][dataset_name] = formatted_score
            inverted_scores[translator][dataset_name] = score

    for translator, scores in inverted_formatted.items():
        lines.append(f'| {translator} | {" | ".join(scores.values())} |')

    img_path = os.path.join(res_dir, 'img', f'{key}.png')
    plot_lang_pair(datasets, inverted_scores, img_path)

    img_relative_path = '/'.join(img_path.split("/")[-2:])
    lines.append(f'\n![Results]({img_relative_path})')


def read_results(res_dir):
    results = defaultdict(dict)
    all_translators = set()
    for bleu_file in glob(res_dir + '/*/*.bleu'):
        dataset_name, translator, = os.path.basename(bleu_file).split('.')[:2]
        pair = bleu_file.split('/')[-2]
        with open(bleu_file) as f:
            score = float(f.read().strip())

        if dataset_name not in results[pair]:
            results[pair][dataset_name] = {}
        results[pair][dataset_name][translator] = score
        all_translators.add(translator)

    # fix missing translators
    for _, datasets in results.items():
        for _, translators in datasets.items():
            for translator in all_translators:
                if translator not in translators:
                    translators[translator] = 0

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
    translators = [t for t in TRANS_ORDER.keys() if t in inverted_scores]

    df = pd.DataFrame(trans_scores, index=datasets, columns=translators)
    fig = df.plot.bar(ylim=(15, None), ylabel='bleu').get_figure()
    fig.set_size_inches(18.5, 10.5)
    fig.savefig(img_path, bbox_inches="tight")


# Main


@click.command()
@click.option('--pairs',
              default='all',
              help='Comma separated language pairs or `all`. Example: es-en,de-et')
@click.option('--translators',
              default='bergamot',
              help='Comma separated translators. Example: bergamot,google')
@click.option('--results-dir',
              help='Directory for results')
@click.option('--models-dir',
              help='Directory with models')
@click.option('--skip-existing',
              default=False,
              is_flag=True,
              help='Whether to skip already calculated scores. '
                   'They are located in `results/xx-xx` folders as *.bleu files.')
def run(pairs, translators, results_dir, models_dir, skip_existing):
    lang_pairs = [(pair[:2], pair[-2:])
                  for pair in (os.listdir(models_dir) if pairs == 'all' else pairs.split(','))]
    print(f'Language pairs to evaluate: {lang_pairs}')
    download_custom_data()
    run_dir(lang_pairs, skip_existing, translators, models_dir=models_dir, results_dir=results_dir)
    build_report(results_dir)


if __name__ == '__main__':
    run()
