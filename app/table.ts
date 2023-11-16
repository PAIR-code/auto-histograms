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
import {css, html, TemplateResult} from 'lit';
import {customElement} from 'lit/decorators';
import {repeat} from 'lit/directives/repeat';

import {state} from './state';
import {styles} from './styles.css';

/**
 * Component
 */
@customElement('table-component')
export class Table extends MobxLitElement {
  static override get styles() {
    return [
      css`
          :host {
            overflow-x: hidden;
            overflow-y: scroll;
            font-family: monospace;
            width: 30%;
            height: 100%;
            background: white;
          }
          .cell {
            border: 1px solid #ddd;
            border-bottom: 0px;
            padding: 10px;
          }
          .token {
            background: lightsalmon;
          }
    `,
      styles
    ];
  }
  constructor() {
    super();
  }


  override render() {
    const {idxsShown, loading} = state;
    if (loading) return '';

    const examplesToRender = idxsShown.length ?
        idxsShown.map(i => state.examples[i]) :
        state.examples;
    return html`
        <div>${
        repeat(
            examplesToRender, (_, i) => i,
            example => this.renderCell(example))}</div>`;
  }

  private renderCell(example: string) {
    const {selectedEntity} = state;
    if (selectedEntity) {
      const htmlPieces: TemplateResult[] = [];
      const textSections = example.toLowerCase().split(selectedEntity);
      textSections.forEach((section, i) => {
        htmlPieces.push(html`${section}`);
        // Unless we're at the last instance.
        if (i < textSections.length - 1) {
          htmlPieces.push(html`<span class='token'>${selectedEntity}</span>`);
        }
      });
      return html`<div class='cell'>${htmlPieces}</div>`;
    }

    return html`<div class='cell'>${example}</div>`;
  }
}
