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

"""Top level agent for data agent multi-agents.

-- it get data from database (e.g., BQ) using NL2SQL
-- then, it use NL2Py to do further data analysis as needed
"""
import json
import logging
import os
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_agent_dir = Path(__file__).parent

def load_config():
    yaml_file = _agent_dir / "agent_settings.yaml"

    # 1. Load .env (Backward Compatibility)
    if load_dotenv():
        logger.info("✅ Loaded .env file")

    # 2. Load YAML (New Config Format)
    if yaml_file.exists():
        try:
            with open(yaml_file, "r") as f:
                yaml_config = yaml.safe_load(f)
            if yaml_config and isinstance(yaml_config, dict):
                for key, value in yaml_config.items():
                    os.environ[str(key)] = str(value)
                logger.info(f"✅ Loaded YAML config from {yaml_file}")
                print(f"env properties loaded: {os.environ}")
        except Exception as e:
            logger.error(f"❌ Failed to load YAML config from {yaml_file}: {e}")

load_config()

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from .prompts import return_instructions_root
from .sub_agents import bqml_agent
from .sub_agents.bigquery.tools import (
    get_database_settings as get_bq_database_settings,
)
from .tools import call_analytics_agent, call_bigquery_agent

# Set up logging
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

# Initialize module-level config variables
_dataset_config = {}
_database_settings = {}
_supported_dataset_types = ["bigquery"]  # BigQuery only
_required_dataset_config_params = ["name", "description"]


def load_dataset_config():
    """Load the dataset configurations for the agent from the config file"""

    dataset_config_file = os.getenv("DATASET_CONFIG_FILE", "")
    if not dataset_config_file:
        _logger.fatal("DATASET_CONFIG_FILE env var not set")

    # If the path is not absolute, make it relative to the agent directory
    # This ensures it works regardless of where the command is run from
    if not os.path.isabs(dataset_config_file):
        dataset_config_file = _agent_dir / dataset_config_file
        _logger.info(f"Resolved dataset config path to: {dataset_config_file}")

    with open(dataset_config_file, "r", encoding="utf-8") as f:
        dataset_config = json.load(f)

    if "datasets" not in dataset_config:
        _logger.fatal("No 'datasets' entry in dataset config")

    for dataset in dataset_config["datasets"]:
        if "type" not in dataset:
            _logger.fatal("Missing dataset type")
        if dataset["type"] not in _supported_dataset_types:
            _logger.fatal("Dataset type '%s' not supported", dataset["type"])

        for p in _required_dataset_config_params:
            if p not in dataset:
                _logger.fatal(
                    "Missing required param '%s' from %s dataset config",
                    p,
                    dataset["type"],
                )

    return dataset_config


def get_database_settings(db_type: str) -> dict:
    """Wrapper function to get database settings by type"""
    assert db_type in _supported_dataset_types
    if db_type == "bigquery":
        return get_bq_database_settings()
    raise ValueError(f"Unsupported database type: {db_type}")


def init_database_settings(dataset_config: dict) -> dict:
    """Initializes the database settings for the configured datasets"""
    db_settings = {}
    for dataset in dataset_config["datasets"]:
        db_settings[dataset["type"]] = get_database_settings(dataset["type"])
    return db_settings


def get_dataset_definitions_for_instructions() -> str:
    """Returns the dataset definitions instructions block"""

    dataset_definitions = """
<DATASETS>
"""
    for dataset in _dataset_config["datasets"]:
        dataset_type = dataset["type"]
        dataset_definitions += f"""
<{dataset_type.upper()}>
<DESCRIPTION>
{dataset["description"]}
</DESCRIPTION>
<SCHEMA>
--------- The schema of the relevant database with a few sample rows. --------
{_database_settings[dataset_type]["schema"]}
</SCHEMA>
</{dataset_type.upper()}>

"""
    dataset_definitions += """
</DATASETS>
"""

    if "cross_dataset_relations" in _dataset_config:
        dataset_definitions += f"""
<CROSS_DATASET_RELATIONS>
--------- The cross dataset relations between the configured datasets. ---------
{_dataset_config["cross_dataset_relations"]}
</CROSS_DATASET_RELATIONS>
"""

    return dataset_definitions


def load_database_settings_in_context(callback_context: CallbackContext):
    """Load database settings into the callback context on first use."""
    if "database_settings" not in callback_context.state:
        callback_context.state["database_settings"] = _database_settings


def get_root_agent() -> LlmAgent:
    tools = [call_analytics_agent]
    sub_agents = []
    for dataset in _dataset_config["datasets"]:
        if dataset["type"] == "bigquery":
            tools.append(call_bigquery_agent)
            sub_agents.append(bqml_agent)

    agent = LlmAgent(
        model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.5-flash"),
        name="skills_agent",
        instruction=return_instructions_root()
        + get_dataset_definitions_for_instructions(),
        global_instruction=(
            f"""
            You are a Skills and L&D Multi Agent System.
            Todays date: {date.today()}
            """
        ),
        sub_agents=sub_agents,  # type: ignore
        tools=tools,  # type: ignore
        before_agent_callback=load_database_settings_in_context,
        generate_content_config=types.GenerateContentConfig(temperature=0.01),
    )

    return agent


# Initialize dataset configurations and database info before the agent starts
_dataset_config = load_dataset_config()
print("loading dataset settings")
_database_settings = init_database_settings(_dataset_config)
print("loaded db settings")


# Fetch the root agent
root_agent = get_root_agent()

from google.adk.apps import App
from google.adk.plugins.global_instruction_plugin import GlobalInstructionPlugin
from google.adk.plugins.logging_plugin import LoggingPlugin

app = App(
    name="skills_agent",
    root_agent=root_agent,
    plugins=[
        LoggingPlugin(),
    ],
)
