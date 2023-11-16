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

"""Run the full pipeline of go/any-histogram.

This includes annotating a dataset in csv form with entities, to clustering
those entities, to labeling them with an LLM.
"""

import json
import os
from typing import Optional

from absl import logging
from automatic_histograms import annotate_entities
from automatic_histograms import cluster
from automatic_histograms import embeddings_manager
from automatic_histograms import llm_manager
from etils import eapp
import numpy as np
import pandas as pd

import shutil

_OUTPUT_HISTOGRAMS_FILENAME = 'histograms.json'
_OUTPUT_DESC_EMBS_FILENAME = 'embeddings_description.npy'
_OUTPUT_ENTITY_EMBS_FILENAME = 'embeddings_entities.npy'
_OUTPUT_ANNOTATED_CSV = 'data.csv'


class AutomaticHistograms:
  """Class for managing and running the automatic histograms pipeline."""

  def __init__(
      self,
      input_csv: str,
      column_to_annotate: str,
      output_directory: str,
      cache_directory: str,
      embedder: Optional[embeddings_manager.Embedder] = None,
      llm: Optional[llm_manager.LLM] = None,
      external_api_key: Optional[str] = None,
  ):
    self._input_csv = input_csv
    self._column_to_annotate = column_to_annotate
    self._output_directory = output_directory
    self._cache_directory = cache_directory

    external = embeddings_manager.DefaultExternalEmbedder
    self._embedder = (
        embedder if embedder else external(api_key=external_api_key)
    )
    self._llm = (
        llm if llm else llm_manager.DefaultExternalLLM(api_key=external_api_key)
    )

  def _load_data(self):
    with open(self._input_csv, 'rb') as f:
      return pd.read_csv(f)

  def _save_histograms_json(
      self,
      histograms=None,
      entities_by_id=None,
      descriptions=None,
      entities=None,
      entity_embs=None,
      description_embs=None,
  ):
    """Saves histogram json data."""
    data = {
        'histograms': histograms,
        'ids_by_entity': entities_by_id,
        'descriptions_embs_order': descriptions,
        'entities_embs_order': entities,
    }
    output_dir = self._output_directory
    histograms_filename = os.path.join(output_dir, _OUTPUT_HISTOGRAMS_FILENAME)
    with open(histograms_filename, 'w') as f:
      f.write(json.dumps(data, indent=2))

    descriptions_filename = os.path.join(output_dir, _OUTPUT_DESC_EMBS_FILENAME)
    self._save_embeddings(description_embs, descriptions_filename)

    entity_embeddings_filename = os.path.join(
        output_dir, _OUTPUT_ENTITY_EMBS_FILENAME
    )
    self._save_embeddings(entity_embs, entity_embeddings_filename)

  def _save_embeddings(self, embs, path):
    with open(path, 'wb') as f:
      np.save(f, embs)

  def _save_annotated_datapoints(self, df: pd.DataFrame):
    output_path = os.path.join(self._output_directory, _OUTPUT_ANNOTATED_CSV)
    with open(output_path, 'wb') as f:
      df.to_csv(f)

  def run_pipeline(self) -> None:
    """Run the full pipeline of go/any-histogram.

    This includes annotating a dataset in csv form with entities, to clustering
    those entities, to labeling them with an LLM.
    """
    eapp.better_logging()

    logging.info('🐍 Loading data')
    # Load in csv.
    df = self._load_data()
    df = parse_df(df, self._column_to_annotate)
    logging.info('🐍 Annotating data')
    df = annotate_entities.annotate_entities(df)

    # Load embeddings cache
    embs_manager = embeddings_manager.EmbeddingsManager(
        self._embedder, self._cache_directory
    )

    # Make the subdir to save outputs.
    output_dir = self._output_directory
    if os.path.exists(output_dir):
      shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    # Save the annotated data.
    self._save_annotated_datapoints(df)

    # Calculate the histograms.
    histograms, entity_embs, entities = cluster.make_histograms(
        df, embs_manager, self._llm
    )

    description_embs, descriptions = cluster.get_histogram_embeddings(
        histograms, embs_manager
    )

    # Save the results.
    logging.info('🐍 Saving data')
    entities_by_id = cluster.get_entities_by_id(df)
    self._save_histograms_json(
        histograms=histograms,
        entities_by_id=entities_by_id,
        descriptions=list(descriptions),
        entities=list(entities),
        entity_embs=entity_embs,
        description_embs=description_embs,
    )

    embs_manager.update_embeddings_cache()


def parse_df(df, col_to_annotate):
  # Keep only the input column, and rename it to "text".
  if col_to_annotate not in df.columns:
    raise Exception(
        f'col_to_annotate ({col_to_annotate}) not found in csv'
        f' headers ({df.columns}).'
    )
  df = df[[col_to_annotate]]
  df = df.rename(columns={col_to_annotate: 'text'})
  return df
