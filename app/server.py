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

"""A demo TypeScript Server with fast edit-refresh for ts / html.

(though you need to restart the server when editing python.)

Will serve index.html at the root, and 'hello world' at /demo.

Usage:
    iblaze run third_party/py/automatic_histograms/app:server
"""

from absl import app
from absl import flags
from automatic_histograms import embeddings_manager
from automatic_histograms import llm_manager
from automatic_histograms.app import server_api
from etils import eapp
from google3.learning.vis.common.tsserver.tsserver import TsServer


_HOST = flags.DEFINE_string(
    'host',
    '0.0.0.0',
    'What host to listen to.'
    'Defaults to serving on 0.0.0.0, set to 127.0.0.1 (localhost) to'
    'disable remote access (also quiets security warnings).',
)

_PORT = flags.DEFINE_integer('port', 5432, 'What port to serve on.')

_SERVER_TYPE = flags.DEFINE_string(
    'server_type',
    'demo',
    'server type corresponding to `/healthz?servertype=str` value. See go/uhc.',
)


def main(unused_argv):
  eapp.better_logging()

  llm = llm_manager.DefaultTmLLM()
  embdder = embeddings_manager.TmEmbedder()

  ts_server = TsServer(
      _HOST.value,
      _PORT.value,
      handlers=server_api.get_handlers(llm, embdder),
      project_root='google3/third_party/py/automatic_histograms/app/',
      index_file='index.html',
      require_auth=True,
      server_type=_SERVER_TYPE.value,
  )
  ts_server.ServeForever()


if __name__ == '__main__':
  app.run(main)
