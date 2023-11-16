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

"""Manager for LLM classes."""


import abc
import google.generativeai as palm
from ratelimit import limits, sleep_and_retry


class LLM(abc.ABC):

  @abc.abstractmethod
  def call(self, text: str) -> str:
    ...

  # TODO(b/294457619) Optimize LLM calls
  def get_label(self, entities_str: str) -> str:
    """Label a set of entities. If no label makes sense, return 'none'."""
    prompt = f"""
  Entities: rollouts, releases/rollouts, link-outs, rollout, rollouts/releases, deliverables/dependencies
  Label: release-related

  Entities: unclear, 1265, good, expected, UpToDate, hot, difficult, tomorrow, Russia
  Label: none

  Entities: Sleep, Making out, Shower, Morning, Funeral, Driving, Eating
  Label: activities

  Entities: Man, Woman, Nonconforming
  Label: genders

  Entities: fabulous, outstanding, interesting, delicious, beautiful, interesting, fascinating, awesome, wonderful
  Label: positive adjectives

  Entities: 1990s, 1970s, Early 2000s, 2000s, 1980s, 1920s, 1980, 1950s, Roaring Twenties
  Label: decades

  Entities: {entities_str}
  Label: """.lower()
    return self.call(prompt)

  def get_examples_of_label(self, label: str) -> list[str]:
    prompt = f"""
  Label: activities
  Entities: Sleep, Making out, Shower, Morning, Funeral, Driving, Eating

  Label: decades
  Entities: 1990s, 1970s, Early 2000s, 1980, 1950s, Roaring Twenties

  Label: subjects
  Entities: English, Post-modernism, Calculous, Robotics, Early french literature

  Label: genders
  Entities: Man, Woman, Nonconforming

  Label: {label}
  Entities:""".lower()

    examples = self.call(prompt).split(", ")
    return examples


class DefaultExternalLLM(LLM):
  def __init__(self, api_key = None):
    palm.configure(api_key=api_key)
  @sleep_and_retry
  @limits(calls=80, period=120)
  def call(self, text):
    return palm.generate_text(prompt=text).result
