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

"""A utility for calculating and caching embeddings."""

import abc
import collections
import os
from typing import Generic, Optional, TypeVar

from absl import logging
import numpy as np
import tensorflow.compat.v2 as tf
import tensorflow_hub as hub
import tqdm

import google.generativeai as palm

_T = TypeVar('_T')
_CACHE_DIRECTORY = '/tmp/any_histogram'
_CACHE_FILENAME = 'cache.npy'

_MAX_CACHE_ENTRIES = 50_000


class Embedder(abc.ABC):
  """A base class for embedding models."""

  @abc.abstractmethod
  def name(self) -> str:
    ...

  @abc.abstractmethod
  def embed(self, text: str) -> np.ndarray:
    ...


class DefaultExternalEmbedder(Embedder):
  def __init__(self, api_key = None):
    palm.configure(api_key=api_key)
  def name(self) -> str:
    return 'models/embedding-gecko-001'
  def embed(self, text: str) -> np.ndarray:
    emb = palm.generate_embeddings(model=self.name(), text=text)['embedding']
    return np.array(emb)


@memoize.Memoize()
def _get_universal_encoder():
  tf.enable_v2_behavior()
  return hub.load('https://tfhub.dev/google/universal-sentence-encoder/4')


class USEEmbedder(Embedder):

  def __init__(self):
    tf.enable_v2_behavior()
    self.encoder = _get_universal_encoder()

  def name(self) -> str:
    return 'USE model'

  def embed(self, text: str) -> np.ndarray:
    return self.encoder([text])[0].numpy()

  def embed_batch(self, text: list[str]) -> np.ndarray:
    return self.encoder(text).numpy()


class EmbeddingsManager:
  """A utility for calculating and caching embeddings."""

  def __init__(
      self,
      model: Embedder,
      cache_directory: str = _CACHE_DIRECTORY,
  ):
    # TODO(b/294456913) use shared embeddings cache / service
    self._cache_directory = cache_directory

    self._model = model

    # Tokens accessed during this run. Used for determining cache evictions.
    self._load_or_create_embeddings_cache()

  def _load_or_create_embeddings_cache(self) -> None:
    """Load the embeddings cache file."""
    if not os.path.exists(self._cache_directory):
      os.makedirs(self._cache_directory)

    logging.info('🐍 Loading cached embeddings.')
    cache_filename = os.path.join(self._cache_directory, _CACHE_FILENAME)
    if os.path.exists(cache_filename):
      with open(cache_filename, 'rb') as f:
        data = np.load(f, allow_pickle=True).item()
    else:
      data = {'cache': {}, 'model_name': self._model.name()}

    loaded_cache = data['cache']

    self._embeddings_cache: LRUCache[np.ndarray] = LRUCache(
        capacity=_MAX_CACHE_ENTRIES, data=loaded_cache
    )

    self.assert_compatibility(data['model_name'])

  def assert_compatibility(self, model_name: str):
    """Assert that the loaded cache matches the model in memory."""
    # Assert that the config matches.
    current_model_name = self._model.name()
    assert current_model_name == model_name, (
        f'Model in memory ({current_model_name}) differs from model used to'
        f' generate cache ({model_name}).'
    )

    # Also do a test embedding to ensure that the embeddings match.
    keys = list(self._embeddings_cache.cache.keys())
    if keys:
      first_key = keys[0]
      cached_embedding = self._embeddings_cache.get(first_key)
      if cached_embedding is not None:
        match = cached_embedding == self._model_embed(first_key)
        assert match.all(), 'Cached embedding did not match model calculation.'

  def update_embeddings_cache(self) -> None:
    """Load the embeddings cache file."""
    logging.info('🐍 Caching embeddings.')
    dict_to_save = self._embeddings_cache.cache
    data = {'cache': dict_to_save, 'model_name': self._model.name()}

    cache_filename = os.path.join(self._cache_directory, _CACHE_FILENAME)
    with open(cache_filename, 'wb') as f:
      np.save(f, data)

  def embed_all(self, texts: list[str]) -> list[np.ndarray]:
    """Embed all texts."""
    try:
      return self._model.embed_batch(texts)  # pytype:disable=attribute-error
    except AttributeError as e:
      logging.warning(
          'Failed to embed texts in batch, falling back on embedding'
          ' element-wise: %s',
          e,
      )
      return [self.embed(text) for text in tqdm.tqdm(texts)]

  # TODO(b/294457194) Optimize embeddings computation (batching, faster
  # embeddings, shared embeddings cache)
  def embed(self, text: str) -> np.ndarray:
    """Get the embedding for a text, either from the cache or the model."""

    # Check the cache.
    emb = self._embeddings_cache.get(text)
    if emb is not None:
      return emb

    # Otherwise, embed with the model.
    emb = self._model_embed(text)
    self._embeddings_cache.put(text, emb)
    return emb

  def _model_embed(self, text: str) -> np.ndarray:
    """Embed a text with the model.."""
    return self._model.embed(text)


class LRUCache(Generic[_T]):
  """LRU Cache dictionary."""

  def __init__(self, capacity: int, data: dict[str, _T]):
    self.cache: collections.OrderedDict[str, _T] = collections.OrderedDict()
    self.capacity = capacity

    self.initialize(data)

  def initialize(self, data: dict[str, _T]) -> None:
    for k, v in data.items():
      self.put(k, v)

  def get(self, key: str) -> Optional[_T]:
    if key not in self.cache:
      return None
    self.cache.move_to_end(key)  # Make the key as the most recently used
    return self.cache[key]

  def put(self, key: str, value: _T) -> None:
    if key in self.cache:
      self.cache.move_to_end(key)  # Update the key as most recently used
    self.cache[key] = value
    if len(self.cache) > self.capacity:
      self.cache.popitem(last=False)  # Remove the least recently used key
