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
"""A standalone library for finding entitities of a specific label in a dataset.

This is an alternative implementation of the "make histogram" functionality in
the automatic histogram server, which does not require running the
pre-annotation pipeline.
"""
from typing import Optional
from absl import logging
from automatic_histograms import annotate_entities
from automatic_histograms import cluster
from automatic_histograms import embeddings_manager
from automatic_histograms import llm_manager
from automatic_histograms import pipeline
from automatic_histograms.app import server_api
import pandas as pd
from sklearn.neighbors import NearestNeighbors


def make_new_histogram(
    category: str,
    column_to_annotate: str,
    df: pd.DataFrame,
    embedder: Optional[embeddings_manager.Embedder] = None,
    llm: Optional[llm_manager.LLM] = None,
    cache_directory: str = '/tmp/auto_histograms_cache',
    entity_label_confidence: float = 0.7,
):
  """Make a histogram of items in the dataset, given a category.

  Args:
    category: type of entities to find in the dataset (e.g., "names")
    column_to_annotate: column of the dataframe to search for entities
    df: pandas dataframe of data
    embedder: model to calculate embeddings
    llm: model to use to generate seed examples of the category
    cache_directory: path directory for caching embeddings
    entity_label_confidence: number between 0 and 1 to set the confidence cutoff
      of which entities are labeled as <category>. Higher is more confident
      (fewer entities will be returned.)

  Returns:
    Dictionary of entities that are instances of the category to the ids of
    datapoints that contain them.
  """
  external = embeddings_manager.DefaultExternalEmbedder
  embedder = (embedder if embedder else external(api_key=external_api_key))
  llm = (
      llm if llm else llm_manager.DefaultExternalLLM(api_key=external_api_key)
  )

  logging.info('🐍 Loading embeddings manager')
  embs_manager = embeddings_manager.EmbeddingsManager(embedder, cache_directory)

  logging.info('🐍 Parsing entities')
  df = pipeline.parse_df(df, column_to_annotate)

  logging.info('🐍 Annotating entities')
  df = annotate_entities.annotate_entities(df)

  logging.info('🐍 Clustering entities')
  duplicated_entities = cluster.take_top_k(cluster.get_duplicated_entities(df))
  entities = cluster.deduplicate(duplicated_entities)

  logging.info('🐍 Training NN retrieval')
  entity_embs = embs_manager.embed_all(list(entities))
  knn = NearestNeighbors(n_neighbors=50)
  knn.fit(entity_embs)

  logging.info('🐍 Calling the LLM to get examples of the labels')
  histogram_items = server_api.get_examples_of_label(
      entities,
      category,
      knn,
      llm=llm,
      embedder=embedder,
      entity_label_confidence=entity_label_confidence,
  )

  ids_by_entity = get_ids_by_entity(df, histogram_items)
  return ids_by_entity


def get_ids_by_entity(df: pd.DataFrame, entities: list[str]):
  """Get a dictionary of entities to ids of datapoints that contain them."""
  ids_by_entity = {}
  for i, row in df.iterrows():
    for entity in row['entities']:
      if entity not in entities:
        continue
      if entity not in ids_by_entity:
        ids_by_entity[entity] = []
      ids_by_entity[entity].append(i)
  return ids_by_entity
