# Automatic histograms

## Motivation

When analyzing an unstructured dataset, it's useful to have histograms over
features you care about. Sometimes (e.g., with [KYD](https://knowyourdata.withgoogle.com/)), these can be provided out of the
box by annotating each datapoint.

However, user data is so specific that we can't know what sort of categories
they care about in advance. E.g., a music dataset might want to see a histogram
over the musicians in the dataset, whereas an RAI fairness dataset might want to
have a histogram of races represented.

How can we do this automatically? Automatic histograms first finds entities in
the data, and then groups and labels them (e.g., to group "covid 19" and
"the flu" under the category "diseases"). 

Additionally, we can allow users to search with the fields, e.g., searching for
"musicians" to create a histogram that they care about in real time.

## Running instructions

Automatic Histograms has two parts. First the data is annotated: for this, we provide a library, or if you prefer, a binary which is a light wrapper around the library. 
Then, the output can be accessed by running a server (see below)
### 1. Annotating data
Your input data should be in csv form. The relevant flags are:

- `--directory` (directory of the input csv, and also where the output files will be written)
- `--input_csv` (name of the csv file)
- `--col_to_annotate` (column in the csv to annotate)


```
$ python3 -m venv auto_histo && . auto_histo/bin/activate && pip install -r automatic_histograms/requirements.txt
$ python -m automatic_histograms.run --palm_api_key_external=<your palm API key>
``` 
Note that running *both* the pipeline and the server require a PaLM API key. See these [instructions](https://makersuite.google.com/app/apikey) on how to get one.


This can also be run programmatically from python (see `run.py`):

```python
  from automatic_histograms import pipeline
  automatic_histograms = pipeline.AutomaticHistograms(
      input_csv=input_csv, 
      column_to_annotate=column,
      output_directory=output_directory,
      cache_directory=cache_directory,
  )
  automatic_histograms.run_pipeline()
```


### 2. Viewing the outputs

To run the demo (either for our pre-annotated data, or your own annotated data)
### Build the typescript/css/html
In a separate terminal window, build the typescript.
```
$ cd automatic_histograms/app
$ yarn && yarn build
```
### Run the python server
```
$ python3 -m venv auto_histo && . auto_histo/bin/activate && pip install -r automatic_histograms/requirements.txt
$ python -m automatic_histograms.app.server_external --palm_api_key_external=<your palm API key>
``` 
Note that running *both* the pipeline and the server require a PaLM API key. See these [instructions](https://makersuite.google.com/app/apikey) on how to get one.


Then navigate to 
`http://localhost:5000/?dir=<your_output_path>`

(If you do not supply a value for `<your_output_path>`, it will default to our demo pre-annotated dataset.)


