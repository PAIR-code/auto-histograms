import collections
from absl import app, flags
from automatic_histograms import embeddings_manager
from automatic_histograms import llm_manager
from automatic_histograms.app.server_api import get_handlers
from flask import Flask, make_response, request, send_file


_PALM_API_KEY_EXTERNAL = flags.DEFINE_string(
    'palm_api_key_external',
    None,
    'The API key for PaLM, used for running externally.',
)


class Handler:

  def respond(self, request, content, content_type, code=200):
    return make_response(content)


def main(argv: collections.abc.Sequence[str]) -> None:
  del argv
  flask_app = Flask(__name__, static_url_path='', static_folder='build')

  @flask_app.route('/')
  def index():
    return send_file('build/index.html')

  api_key = _PALM_API_KEY_EXTERNAL.value
  llm = llm_manager.DefaultExternalLLM(api_key=api_key)
  embedder = embeddings_manager.DefaultExternalEmbedder(api_key=api_key)
  default_handler = Handler()
  for route, handler in get_handlers(llm, embedder).items():
    flask_app.add_url_rule(
        route,
        route,
        view_func=handler,
        defaults={'request': request, 'handler': default_handler},
    )
  flask_app.run(debug=True, host='0.0.0.0')


if __name__ == '__main__':
  app.run(main)
