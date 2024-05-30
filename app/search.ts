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

// tslint:disable:g3-no-void-expression

import {MobxLitElement} from '@adobe/lit-mobx';
import {css, html} from 'lit';
import {customElement} from 'lit/decorators';

import {styles as loadingStyles} from './loading_styles.css';
import {state} from './state';
import {styles} from './styles.css';

const DELAY = 500;
/**
 * Component for rendering histogram search.
 */
@customElement('histogram-search-component')
export class Search extends MobxLitElement {
  static override get styles() {
    return [
      css`
      :host {
        display: flex;
        align-items: center;
      }
      input {
        padding: 5px;
        margin: 10px;
        width: 200px;
      }
      .holder {
        position: relative;
      }
      button {
        margin: 5px;
        cursor: pointer;
      }
    `,
      styles, loadingStyles
    ];
  }

  private onKeystroke(e: Event) {
    const target = e.target as HTMLInputElement;
    const search = target.value;
    state.selectedEntities = [];

    const searchIfNotStale = () => {
      const freshSearch = target.value;
      if (freshSearch !== search) return;
      state.currSearch = freshSearch;
      if (!state.currSearch) {
        state.currSearchResults = [];
        state.cancelPendingHistogram();
        return;
      }
      state.searchHistograms();
    };

    setTimeout(searchIfNotStale, DELAY);
  }


  override render() {
    return html`
        <div class=holder>
          <input type="text" placeholder="Search histograms..." name="search" autocomplete="off" 
            @input=${(e: Event) => this.onKeystroke(e)}>
        </div>
        or 
        <button .disabled=${state.loadingNewHistogram} @click=${
        () => state.makeNewHistogram()}> Create a new histogram</button>
        ${this.maybeRenderLoading()}
        `;
  }

  private maybeRenderLoading() {
    if (!state.loadingNewHistogram) return null;
    return html`<div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div>`;
  }
}
