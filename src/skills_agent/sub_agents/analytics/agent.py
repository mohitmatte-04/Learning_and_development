# Copyright 2025 Google LLC
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

"""Analytics Agent: generate nl2py and use code interpreter to run the code."""
import os

from google.adk.agents import Agent
print("importing vertexaicodeexecutor")
from google.adk.code_executors import VertexAiCodeExecutor, BaseCodeExecutor
print("imported vertexaicodeexecutor")
print("importing prompts")
from .prompts import return_instructions_analytics
print("imported prompts")
print("creating analytics agent")

# Mock for testing without credentials
class MockCodeExecutor(BaseCodeExecutor):
    def __init__(self, *args, **kwargs):
        pass
    def execute_code(self, code, **kwargs):
        return "Code execution mocked."

project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
# Check for placeholder or empty project ID
is_mock_mode = project_id == "YOUR_PROJECT_ID" or not project_id

if is_mock_mode:
    print(f"WARNING: Using MockCodeExecutor for Analytics Agent. Project ID: {project_id}")
    code_executor = MockCodeExecutor()
else:
    # Use env var for resource name or fallback
    resource_name = os.getenv(
        "CODE_INTERPRETER_EXTENSION_NAME",
        "projects/36231825761/locations/us-central1/extensions/3673077265857511424"
    )
    try:
        code_executor = VertexAiCodeExecutor(
            resource_name=resource_name,
            optimize_data_file=True,
            stateful=True,
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        )
    except Exception as e:
        print(f"WARNING: Failed to init VertexAiCodeExecutor: {e}. Falling back to Mock.")
        code_executor = MockCodeExecutor()

analytics_agent = Agent(
    model=os.getenv("ANALYTICS_AGENT_MODEL", ""),
    name="analytics_agent",
    instruction=return_instructions_analytics(),
    code_executor=code_executor,
)
print("created analytics agent")

