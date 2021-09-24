import re
from io import StringIO
import pandas as pd
from spellchecker import SpellChecker
import streamlit as st

spell = SpellChecker()


def check_spelling(files_dict, okay_words=None):
    misspelled_line = []
    misspelled_word = []
    file_name = []

    if not okay_words:
        okay_words = []

    for name, contents in files_dict.items():
        file_lines = contents.splitlines()

        for line in file_lines:
            if line.strip() and not line.startswith('#'):
                og_line = line

                if line.startswith(','):
                    end = len(line)
                    matches = re.finditer('[,][0-9]', line)
                    for match in matches:
                        end = match.start()
                    line = line[1:end]

                line = line.replace('...', '.')
                line = line.replace('</', '')
                line = line.replace(" '", ' ')
                line = line.replace("' ", ' ')
                line = re.sub('/[A-Z_]+}', '}', line)
                line = re.sub('[~"^|{}<>*]|NoPUNCT|NoCAPS|PIPESYM', '', line)
                line = re.sub(r'\[[0-9A-Za-z/;_]+\]', ' ', line)
                line = line.replace('/', ' ')
                line = line.replace('〽️', ' ')
                line = re.sub(' +', ' ', line)

                words = [w.strip(" '") for w in re.split(r'[\s,.!?—()-:]', line)
                         if w.strip() and not w.startswith('[') and w != '|' and '_' not in w]
                words = words[1:]

                misspelled = spell.unknown(words)
                misspelled = [m for m in misspelled if any([ch.isalpha() for ch in list(m)]) and len(m) > 1
                              and m not in okay_words]
                if misspelled:
                    misspelled_line += [og_line]
                    misspelled_word += ['; '.join(misspelled)]
                    file_name += [name]

    df = pd.DataFrame()
    df['File'] = file_name
    df['Phrase'] = misspelled_line
    df['Possible misspellings'] = misspelled_word

    return df


st.title("Spelling check")
raw_files = st.file_uploader('Select syn and lex files', accept_multiple_files=True, key='files')
files = {}
for f in raw_files:
    # To read file as bytes:
    bytes_data = f.getvalue()
    # To convert to a string based IO:
    stringio = StringIO(f.getvalue().decode("utf-8"))
    # To read file as string:
    string_data = stringio.read()
    files[f.name] = string_data

if files:
    spelling_df = check_spelling(files)
    ignore_words = st.multiselect('Words to ignore', set(spelling_df['Possible misspellings']))
    if ignore_words:
        spelling_df = check_spelling(files, okay_words=ignore_words)
    st.dataframe(spelling_df)
