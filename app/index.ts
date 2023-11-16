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

import './table';
import './histograms';

import {MobxLitElement} from '@adobe/lit-mobx';
import {css, html} from 'lit';
import {customElement} from 'lit/decorators';

import {state} from './state';
import {styles} from './styles.css';

/**
 * Component
 */
@customElement('app-component')
export class Component extends MobxLitElement {
  static override get styles() {
    return [
      css`
      :host {
        font-family: Inter,Roboto,Helvetica Neue;
        font-size: 12px;
        color: #333;
        margin: 0;
        background: #efefef;
      }
      .content {
        display: flex;
        height: 95vh;
      }
      .header {
        padding: 10px;
        background: tomato;
        color: white;
        font-size: 15px;
        display: flex;
        justify-content: space-between;
        font-weight: bold;
        text-transform: uppercase;
      }
      .numExamples {
        opacity: .7;
        font-size: x-small;
      }
      .info {
        display: flex;
        align-items: center;
        color: darkred;
      }
      a {
        text-transform: none;
      }
      `,
      styles
    ];
  }

  override render() {
    const {path, datasetName, numExamples} = state;
    return html`
        <div class='header'>
        
          <div title=${path}>${datasetName}
            <span class='numExamples'>(${numExamples} examples)</span>
          </div> 

          <div class='info'>
            <div>Auto histograms</div> 
            <a target='_blank' href="http://go/any-histogram"><span class="material-icons">open_in_new</span></a>
          </div>
        </div>
        <div class='content'> 
          <table-component></table-component>
          <histograms-component></histograms-component>
        </div>
      `;
  }
}
