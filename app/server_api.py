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

"""Server methods."""
import functools
import json
import logging
import os

from automatic_histograms import embeddings_manager
from automatic_histograms import llm_manager
import numpy as np
from scipy.spatial.distance import minkowski
from sklearn.neighbors import NearestNeighbors

_K = 20
_DIST_CUTOFF = 0.5
_ENTITY_LABEL_CONFIDENCE = 0.7


def load_json_data(data_dir: str):
  path = os.path.join(data_dir, 'histograms.json')
  with open(path, 'r') as f:
    data = f.read()
  return json.loads(data)


def load_embeddings(embs_file: str, data_dir: str):
  path = os.path.join(data_dir, embs_file)
  with open(path, 'rb') as f:
    embs = np.load(f)
  knn = NearestNeighbors(n_neighbors=_K)
  knn.fit(embs)
  return knn


def get_histograms(handler, request):
  data_dir = _get_dir(request)
  histograms = load_json_data(data_dir)
  return handler.respond(request, json.dumps(histograms), 'text/json', 200)


def get_data(handler, request):
  data_dir = _get_dir(request)
  path = os.path.join(data_dir, 'data.csv')
  with open(path, 'r') as f:
    csv_data = f.read()
  return handler.respond(request, csv_data, 'text/csv', 200)


def search_histograms(handler, request, embedder: embeddings_manager.Embedder):
  """Searches histograms."""
  data_dir = _get_dir(request)
  search = request.args.get('search')

  histograms = load_json_data(data_dir)
  knn = load_embeddings('embeddings_description.npy', data_dir)
  descriptions = histograms['descriptions_embs_order']

  emb = embedder.embed(search)
  k = min(len(descriptions), _K)
  dists, idxs = knn.kneighbors([emb], n_neighbors=k)

  search_results = []
  for dist, idx in zip(dists[0], idxs[0]):
    if dist < _DIST_CUTOFF:
      search_results.append(descriptions[idx])

  response = json.dumps({'search_results': search_results})
  return handler.respond(request, response, 'text/json', 200)


def get_examples_of_label(
    entities,
    description,
    knn_entities,
    llm: llm_manager.LLM,
    embedder: embeddings_manager.Embedder,
    entity_label_confidence: float,
    n_neighbors: int = _K,
):
  """Gets examples of label."""
  logging.info('🐍 Getting exemplars')
  examples_of_label = llm.get_examples_of_label(description)
  logging.info(
      '🐍 Exemplars generated for "%s": %s',
      description,
      ', '.join(examples_of_label),
  )

  logging.info('🐍 Embedding exemplars')
  embs = np.array([embedder.embed(ex) for ex in examples_of_label])
  logging.info('🐍 Done embedding exemplars')

  logging.info('🐍 Calculating neighbors')
  examples_mean_emb = np.mean(embs, axis=0)
  dists_to_center = [minkowski(emb, examples_mean_emb) for emb in embs]

  # The distance cutoff for labeling an entity as an example of the query.
  eps = 1 - entity_label_confidence
  radius = np.max(dists_to_center) * (1 + eps)

  k = min(len(entities), n_neighbors)
  dists, idxs = knn_entities.kneighbors([examples_mean_emb], n_neighbors=k)
  answers = []
  for dist, idx in zip(dists[0], idxs[0]):
    if dist > radius:
      break
    answers.append(entities[idx])

  logging.info('🐍 Calculated neighbors')
  return answers


def make_new_histogram(
    handler,
    request,
    llm: llm_manager.LLM,
    embedder: embeddings_manager.Embedder,
):
  """Makes a new histogram."""
  new_histogram_name = request.args.get('new_histogram_name')
  data_dir = _get_dir(request)

  histograms = load_json_data(data_dir)
  knn_entities = load_embeddings('embeddings_entities.npy', data_dir)
  entities = histograms['entities_embs_order']

  histogram_items = get_examples_of_label(
      entities,
      new_histogram_name,
      knn_entities,
      llm,
      embedder,
      _ENTITY_LABEL_CONFIDENCE,
  )
  response = json.dumps({new_histogram_name: histogram_items})
  return handler.respond(request, response, 'text/json', 200)


def _get_dir(request) -> str:
  return request.args.get('dir')


def get_handlers(llm: llm_manager.LLM, embedder: embeddings_manager.Embedder):
  return {
      '/get_histograms': get_histograms,
      '/get_data': get_data,
      '/search_histograms': functools.partial(
          search_histograms, embedder=embedder
      ),
      '/make_new_histogram': functools.partial(
          make_new_histogram, llm=llm, embedder=embedder
      ),
  }
