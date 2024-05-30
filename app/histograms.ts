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

import './search';

import {MobxLitElement} from '@adobe/lit-mobx';
import {css, html, TemplateResult} from 'lit';
import {customElement} from 'lit/decorators';
import {classMap} from 'lit/directives/class-map';
import {repeat} from 'lit/directives/repeat';
import {styleMap} from 'lit/directives/style-map';

import {styles as loadingStyles} from './loading_styles.css';
import {state} from './state';
import {styles} from './styles.css';

/**
 * Component
 */
@customElement('histograms-component')
export class Histograms extends MobxLitElement {
  static override get styles() {
    return [
      css`
      :host {
        width: 70%;
        overflow: auto;
        height: 100%;
      }
      .all-histograms-holder {
        display: flex;
        flex-wrap: wrap;
      }
      .histogram-holder {
        margin: 13px;
        padding: 12px 0px;
        border-radius: 10px;
        background: white;
        box-shadow: rgba(99, 99, 99, 0.2) 0px 2px 8px 0px;
      }
      .is-pending {
        box-shadow: rgba(0, 0, 0, 0.3) 0px 19px 38px, rgba(0, 0, 0, 0.22) 0px 15px 12px;
      }
      .table-holder {
        overflow: auto;
        max-height: 200px;
        overflow-x: hidden;
        padding: 0 12px;
      }
      .disabled {
        opacity: .5;
        pointer-events: none;
      }
      .title {
        text-transform: uppercase;
        font-size: larger;
        font-weight: bold;
        text-align: center;
        color: tomato;
        padding-bottom: 9px;
        cursor: pointer;
      }
      .user-created {
        color: darkred;
      }
      .unhighlighted {
        font-weight: lighter;
      }
      .bar {
        background: lightsalmon;
        padding: 2px;
        font-size: smaller;
        color: darkred;
        line-height: initial;
      }
      .entity {
        text-align: right;
        max-width: 150px;
        text-overflow: ellipsis;
        white-space: nowrap;
        overflow: hidden;
      }
      .is-pending .entity {
        text-align: left;
      }
      tr {
        cursor: pointer;
      }
      .selected .bar, tr:hover .bar {
        background: tomato;
      }
      .selected .entity, tr:hover .entity {
        color: tomato;
      }
      .button-holder {
        display: flex;
        padding: 0 10px;
      }
      .instructions {
        font-size: smaller;
        color: #666;
        padding: 0 16px;
        font-style: italic;
      }
    `,
      styles, loadingStyles
    ];
  }

  override render() {
    if (state.loading) return this.renderLoading();

    const numEntitiesFirstBin = (description: string) => {
      const entity = state.histograms[description][0];
      if (!entity) return 0;
      return state.idsByEntitity[entity].length;
    };

    const sortedHistogramKeys = state.userCreatedHistogramKeys.concat(
        Object.keys(state.histograms)
            .sort((a, b) => numEntitiesFirstBin(b) - numEntitiesFirstBin(a)));

    // Render only the descriptions that contain the current search
    const stringMatchedHistograms = sortedHistogramKeys.filter(
        description => description.includes(state.currSearch));

    const searchResults = state.currSearchResults.filter(
        result => !stringMatchedHistograms.includes(result));
    const searchedHistograms = stringMatchedHistograms.concat(searchResults);
    const finalSortOrder = [...new Set(searchedHistograms)];

    const click = () => state.selectedEntities = [];
    return html`
        <histogram-search-component></histogram-search-component>
        <div class='all-histograms-holder' @click=${click}>${
        repeat(
            finalSortOrder, (description) => description,
            (description) => this.renderHistogram(description))}</div>`;
  }

  private renderAcceptDeleteButtons(isPending: boolean) {
    if (!isPending) return html``;
    const disabled = state.pendingHistogramEntities.size === 0;

    return html`
      <div class='instructions'>Select entities to create a new histogram.</div>
      <div class='button-holder'>
        <button .disabled=${disabled} @click=${
        () => state.acceptPendingHistogram()}>create</button>
        <button @click=${() => state.cancelPendingHistogram()}>cancel</button>
      </div>`;
  }

  private renderHistogram(description: string) {
    const isPending = state.pendingHistogram === description;
    const isDisabled = !!state.pendingHistogram && !isPending;

    const entities = state.histograms[description] || [];
    const counts = entities.map(entity => state.idsByEntitity[entity].length);
    const maxCount = Math.max(...counts);
    const descriptionHtml = this.renderDescription(description, entities);
    const buttons = this.renderAcceptDeleteButtons(isPending);
    const entitiesHtml = html`
        <div class='table-holder'>
        <table>${
        repeat(
            entities, entity => entity,
            entity => this.renderBar(entity, maxCount, isPending))}</table>
            </div>`;

    const classes = classMap({
      'is-pending': isPending,
      'histogram-holder': true,
      'disabled': isDisabled
    });
    return html`
        <div class=${classes}>
          ${descriptionHtml}
          ${buttons}
          ${entitiesHtml}
        </div>`;
  }

  private renderDescription(description: string, entities: string[]) {
    const selectAll = (e: Event) => {
      e.stopPropagation();
      const alreadySelected = state.selectedEntities === entities;
      state.selectedEntities = alreadySelected ? [] : entities;
    };

    const isUserCreated = state.userCreatedHistogramKeys.includes(description);
    const classes = classMap({'title': true, 'user-created': isUserCreated});
    if (!state.currSearch)
      return html`<div class=${classes} @click=${selectAll}>${
          description}</div>`;

    // If there is a current search, highlight the parts of the word that match
    // that search.
    const htmlPieces: TemplateResult[] = [];
    const textSections = description.toLowerCase().split(state.currSearch);
    textSections.forEach((section, i) => {
      htmlPieces.push(html`<span class='unhighlighted'>${section}</span>`);
      // Unless we're at the last instance.
      if (i < textSections.length - 1) {
        htmlPieces.push(html`<span>${state.currSearch}</span>`);
      }
    });
    return html`<div class=${classes} @click=${selectAll}>${htmlPieces}</div>`;
  }

  private renderBar(entity: string, totalWidth: number, isPending: boolean) {
    const numExamples = state.idsByEntitity[entity].length;
    const width = numExamples / totalWidth * 100;
    const style = styleMap({'width': `${width}px`});

    const isSelected = state.selectedEntities.includes(entity);
    const entityIsPending =
        isPending && state.pendingHistogramEntities.has(entity);

    const onInputChecked = (e: Event) => {
      if ((e?.target as HTMLInputElement)?.value) {
        state.pendingHistogramEntities.add(entity);
      } else {
        if (state.pendingHistogramEntities.has(entity)) {
          state.pendingHistogramEntities.delete(entity);
        }
      }
    };

    const toggle =
        isPending ? html`<input @click=${onInputChecked} type="checkbox">` : '';

    // Select or deselect the entity on click.
    const clicked = (e: Event) => {
      e.stopPropagation();
      if (isPending) return;
      if (isSelected) {
        state.selectedEntities.splice(
            state.selectedEntities.indexOf(entity), 1);
      } else {
        state.selectedEntities.push(entity);
      }
    };

    const bar = isPending ?
        '' :
        html`<div class='bar' style=${style}>${numExamples}</div>`;

    const classes =
        classMap({'selected': isSelected, 'entity-pending': entityIsPending});
    return html`
        <tr class=${classes} @click=${clicked}>
          <td>${toggle}</td>
          <td><div class='entity' title=${entity}>${entity}</div></td>
          <td>${bar}</td>
        </tr>`;
  }


  private renderLoading() {
    return html`<div class="lds-ring"><div></div><div></div><div></div><div></div></div>`;
  }
}
