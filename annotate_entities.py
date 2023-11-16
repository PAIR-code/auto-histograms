# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Annotate the entities for each item in a dataset."""

import nltk
import tqdm

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')


stopwords = nltk.corpus.stopwords
WordNetLemmatizer = nltk.stem.WordNetLemmatizer


def get_entities(lemmatizer, stop_words, text: str):
  text = nltk.pos_tag(nltk.word_tokenize(text))
  entities = []
  for word, pos in text:
    word = lemmatizer.lemmatize(word).lower()
    # Ignores stopwords ('the', 'in', etc) and verbs.
    # Only keeps non-cardinal numbers (e.g., dates) and nouns.
    if 'NN' in pos or 'NUM' in pos or 'CD' in pos and word not in stop_words:
      entities.append(word)
  return list(dict.fromkeys(entities))


def annotate_entities(df):
  """Annotate entities."""
  df['entities'] = ''
  df = df.fillna('')
  lemmatizer = WordNetLemmatizer()
  stop_words = set(stopwords.words('english'))

  for index, row in tqdm.tqdm(df.iterrows()):
    text = row['text']
    entities = get_entities(lemmatizer, stop_words, text)
    df['entities'][index] = entities
  return df
