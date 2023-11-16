/**
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// tslint:disable:no-new-decorators
import * as d3 from 'd3';
import {computed, observable} from 'mobx';
const DEFAULT_PATH = 'test_data/data.cvs'


interface Histogram {
  [description: string]: string[];
}
interface IdsByEntitity {
  [entity: string]: number[];
}

/**
 * Core application state.
 */
export class State {
  @observable histograms: Histogram = {};
  @observable pendingHistogram?: string = undefined;
  @observable pendingHistogramEntities = new Set<string>();
  @observable idsByEntitity: IdsByEntitity = {};
  @observable examples: string[] = [];
  @observable loadingNewHistogram = false;
  @observable loading = true;
  @observable currSearch = '';
  @observable currSearchResults: string[] = [];
  @observable selectedEntity = '';

  @computed
  get idxsShown(): number[] {
    return this.idsByEntitity[this.selectedEntity] || [];
  }

  readonly path: string = this.getPathFromUrl();

  @computed
  get datasetName() {
    // Filter for '' in case the path ends in '/'.
    const pathParts = this.path.split('/').filter((dir: string) => dir);
    return pathParts.pop();
  }
  @computed
  get numExamples() {
    return this.examples.length;
  }
  constructor() {
    this.getData();
  }

  async searchHistograms() {
    const url = `/search_histograms?search=${this.currSearch}&dir=${this.path}`;
    // tslint:disable-next-line:no-any
    const rawRes = await d3.json(url) as any;
    this.loading = true;
    this.currSearchResults = rawRes['search_results'];
    this.loading = false;
  }

  async makeNewHistogram() {
    this.loadingNewHistogram = true;
    const url = `/make_new_histogram?new_histogram_name=${
        this.currSearch}&dir=${this.path}`;
    // tslint:disable-next-line:no-any
    const rawResult = await d3.json(url) as any;
    this.histograms[this.currSearch] = rawResult[this.currSearch];
    this.pendingHistogram = this.currSearch;
    this.loadingNewHistogram = false;
  }

  acceptPendingHistogram() {
    if (!this.pendingHistogram) return;
    const entities = [...this.pendingHistogramEntities].sort(
        (a: string, b: string) =>
            state.idsByEntitity[b].length - state.idsByEntitity[a].length);
    this.histograms[this.pendingHistogram] = entities;
    this.clearPendingHistogram();
  }
  cancelPendingHistogram() {
    const key = this.pendingHistogram;
    if (key && this.histograms.hasOwnProperty(key)) {
      delete this.histograms[key];
    }
    this.currSearch = '';
    this.clearPendingHistogram();
  }

  private clearPendingHistogram() {
    this.pendingHistogram = undefined;
    this.pendingHistogramEntities = new Set();
  }

  private async getData() {
    const dataPath = `/get_histograms?dir=${this.path}`;
    // tslint:disable-next-line:no-any
    const data = await d3.json(dataPath) as any;
    this.histograms = data['histograms'];
    this.idsByEntitity = data['ids_by_entity'];

    const csvPath = `/get_data?dir=${this.path}`;
    const csv = await d3.csv(csvPath);
    // tslint:disable-next-line:no-any
    this.examples = csv.map((ex: any) => ex['text']);

    this.loading = false;
  }

  private getPathFromUrl() {
    const url = new URL(location.href).searchParams.get('dir');
    if (!url) {
      window.location.search = `?dir=${DEFAULT_PATH}`;
    }
    return url || DEFAULT_PATH;
  }
}

// tslint:disable-next-line:enforce-comments-on-exported-symbols
export const state = new State();
