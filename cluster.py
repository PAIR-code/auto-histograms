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

"""Functions for clustering entities, and labeling those clusters."""

import collections
import collections.abc
import itertools

from absl import logging
from automatic_histograms import embeddings_manager
from automatic_histograms import llm_manager
import numpy as np
from scipy.cluster import hierarchy
import tqdm


SIMILARITY_THRESHOLD = 0.05


def get_duplicated_entities(df):
  """Get all entities across the dataset."""
  entities = df['entities'].values
  return list(itertools.chain(*entities))


def deduplicate(duplicated_entities):
  """Deduplicate the entities and save as an np array."""
  return np.array(list(set(duplicated_entities)))


def get_embedding_matrix(all_embeddings):
  """Calculate the embedding distance matrix."""
  norm = np.linalg.norm(all_embeddings, axis=-1, keepdims=True)
  normalized_embeddings = all_embeddings / norm
  emb_similarities = np.dot(normalized_embeddings, normalized_embeddings.T)
  emb_distances = 1 - emb_similarities
  return emb_distances


def _get_clusters(emb_distances, entities):
  """Calculate the clusters using heirarichal clustering."""
  # Note that we oversample clusters, that is, any given entity will appear in
  # many clusters.
  linkage_tree = hierarchy.linkage(emb_distances, 'median')

  all_clusters_dict = {}

  for k in tqdm.tqdm(range(len(entities))):
    cluster_labels = hierarchy.fcluster(linkage_tree, k, criterion='maxclust')
    for i in range(max(cluster_labels) + 1):
      cluster = entities[cluster_labels == i]
      if len(cluster) < 3 or len(cluster) > 15:
        continue
      key = ''.join(cluster)
      if key in all_clusters_dict:
        continue
      all_clusters_dict[key] = cluster

  return [list(c) for c in all_clusters_dict.values()]


def get_entities_by_id(df):
  """For all entities, find all ids that have that entity."""
  ids_by_entity = {}
  for i, df_entities in enumerate(df['entities']):
    for entity in df_entities:
      if entity not in ids_by_entity:
        ids_by_entity[entity] = []
      ids_by_entity[entity].append(i)
  return ids_by_entity


def _sort_cluster_by_counts(cluster, entity_counts):
  """Sort the cluster with the largest buckets first."""
  return sorted(cluster, key=lambda entity: entity_counts[entity], reverse=True)


def _label_and_combine_clusters(
    all_clusters, entity_counts, llm: llm_manager.LLM
):
  """Label the clusters. Combine multiple clusters with the same label."""
  histograms = {}
  for cluster in tqdm.tqdm(all_clusters):
    if cluster:
      sorted_cluster = _sort_cluster_by_counts(cluster, entity_counts)
      cluster_str = ', '.join(sorted_cluster[:15])
      description = llm.get_label(cluster_str)
      if description == 'none' or not description or description == 'None':
        continue

      if description not in histograms:
        histograms[description] = []
      histograms[description] += list(cluster)

  # Since we concatenated the histograms, sort again.
  for description, cluster in histograms.items():
    cluster = list(set(cluster))
    histograms[description] = _sort_cluster_by_counts(cluster, entity_counts)
  return histograms


def _combine_clusters_using_centroids(all_clusters, entity_embs, entities):
  """Combines clusters using centroids."""
  embs_dict = {entity: entity_embs[i] for i, entity in enumerate(entities)}

  # Get the centroids for all clusters.
  cluster_centroids = []
  for cluster in all_clusters:
    cluster_embs = np.array([embs_dict[e] for e in cluster])
    cluster_centroids.append(np.mean(cluster_embs, axis=0))

  # Combine those that are very similar to each other.
  cluster_sims = get_embedding_matrix(cluster_centroids)
  deduped_clusters = []
  combined_indices = []
  for i, cluster in enumerate(all_clusters):
    if i in combined_indices:
      continue
    deduped_cluster = cluster
    for j, other_cluster in enumerate(all_clusters):
      if i >= j or j in combined_indices:
        continue
      sim = cluster_sims[i, j]
      if sim < SIMILARITY_THRESHOLD:
        deduped_cluster += other_cluster
        combined_indices.append(j)

    deduped_clusters.append(list(set(deduped_cluster)))
  return deduped_clusters


def take_top_k(duplicated_entities, k=2000):
  entity_counts = list(dict(collections.Counter(duplicated_entities)).items())
  entity_counts = sorted(entity_counts, key=lambda x: x[1], reverse=True)[:k]
  return {entity: count for entity, count in entity_counts}


def get_histogram_embeddings(
    histograms, embs_manager: embeddings_manager.EmbeddingsManager
):
  """Get embeddings for histogram labels."""

  # Embed entities
  logging.info('🐍 Embedding descriptions')
  descriptions = list(histograms.keys())
  description_embs = embs_manager.embed_all(descriptions)
  return description_embs, descriptions


def make_histograms(
    df, embs_manager: embeddings_manager.EmbeddingsManager, llm: llm_manager.LLM
):
  """Generate histograms from a df pre-annotated with entities."""
  # Load data
  duplicated_entities = get_duplicated_entities(df)
  duplicated_entities = take_top_k(duplicated_entities)
  entity_counts = dict(collections.Counter(duplicated_entities))
  entities = deduplicate(duplicated_entities)

  # Embed entities
  logging.info('🐍 Embedding entities')
  entity_embs = embs_manager.embed_all(list(entities))
  embs_manager.update_embeddings_cache()
  emb_distances = get_embedding_matrix(entity_embs)

  # Cluster the entities (oversampling-- entities will be in many clusters.)
  logging.info('🐍 Clustering entities')
  all_clusters = _get_clusters(emb_distances, entities)

  all_clusters = _combine_clusters_using_centroids(
      all_clusters, entity_embs, entities
  )
  logging.info('🐍 Labeling clusters')
  histograms = _label_and_combine_clusters(all_clusters, entity_counts, llm)

  # Return histograms.
  return histograms, entity_embs, entities
