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

To run:
blaze run third_party/py/automatic_histograms:run -- --alsologtostderr
"""

import collections
import collections.abc
import os

from absl import app
from absl import flags
from automatic_histograms import pipeline

_DIRECTORY = flags.DEFINE_string(
    'directory',
    'automatic_histograms/test_data',
    'Experiment directory.',
)

_INPUT_CSV = flags.DEFINE_string(
    'input_csv',
    'test_data.csv',
    'Input csv with the original data. Outputs will be stored in a subfolder'
    ' with the same name.',
)

_COL = flags.DEFINE_string(
    'col_to_annotate',
    'input',
    'Column in the dataframe to annotate and create histograms for.',
)

_CACHE_DIRECTORY = flags.DEFINE_string(
    'cache_directory',
    '/tmp/automatic_histograms/cache',
    'The directory to cache embeddings to.',
)

_PALM_API_KEY_EXTERNAL = flags.DEFINE_string(
    'palm_api_key_external',
    None,
    'The API key for PaLM, used for running externally.',
)


def main(argv: collections.abc.Sequence[str]) -> None:
  del argv
  input_csv = os.path.join(_DIRECTORY.value, _INPUT_CSV.value)
  column = _COL.value
  subdir_name = _INPUT_CSV.value.replace('.csv', '')
  output_directory = os.path.join(_DIRECTORY.value, subdir_name, column)

  automatic_histograms = pipeline.AutomaticHistograms(
      input_csv=input_csv,
      column_to_annotate=column,
      output_directory=output_directory,
      cache_directory=_CACHE_DIRECTORY.value,
      external_api_key=_PALM_API_KEY_EXTERNAL.value,
  )
  automatic_histograms.run_pipeline()


if __name__ == '__main__':
  app.run(main)
