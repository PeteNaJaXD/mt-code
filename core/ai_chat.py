"""AI Chat integration with multiple provider support."""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any
import logging

from core.paths import LOG_FILE_STR
from core.ai_config import get_ai_config

logging.basicConfig(
    filename=LOG_FILE_STR,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class AIProvider(ABC):
    """Base class for AI providers."""

    name: str = "base"
    display_name: str = "Base Provider"

    def __init__(self, project_root: str, get_editor_content: Callable[[], str] = None):
        self.project_root = project_root
        self.get_editor_content = get_editor_content
        self.messages = []

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available (API key set, etc.)."""
        pass

    @abstractmethod
    async def send_message(self, user_message: str, on_chunk: Callable[[str], None] = None) -> str:
        """Send a message and get a response."""
        pass

    async def send_completion(self, prompt: str) -> str:
        """Send a stateless completion request (no history, no tools).

        Used for inline completions where we don't want to accumulate
        conversation history or include tool definitions.
        """
        # Default implementation uses send_message, but providers should override
        # to avoid history accumulation
        return await self.send_message(prompt)

    def clear_history(self):
        """Clear conversation history."""
        self.messages = []

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for the provider."""
        return []

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return the result."""
        try:
            if tool_name == "read_file":
                return self._read_file(tool_input.get("path", ""))
            elif tool_name == "list_files":
                return self._list_files(tool_input.get("path", "."))
            elif tool_name == "get_current_editor":
                return self._get_current_editor()
            elif tool_name == "search_files":
                return self._search_files(
                    tool_input.get("pattern", ""),
                    tool_input.get("file_pattern", "*")
                )
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def _read_file(self, path: str) -> str:
        """Read a file from the project."""
        full_path = Path(self.project_root) / path
        if not full_path.exists():
            return f"File not found: {path}"
        if not full_path.is_file():
            return f"Not a file: {path}"
        try:
            full_path.resolve().relative_to(Path(self.project_root).resolve())
        except ValueError:
            return "Access denied: path outside project root"

        try:
            content = full_path.read_text(errors='replace')
            if len(content) > 50000:
                content = content[:50000] + "\n... (truncated)"
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _list_files(self, path: str) -> str:
        """List files in a directory."""
        full_path = Path(self.project_root) / path
        if not full_path.exists():
            return f"Directory not found: {path}"
        if not full_path.is_dir():
            return f"Not a directory: {path}"

        try:
            items = []
            for item in sorted(full_path.iterdir()):
                if item.name.startswith('.'):
                    continue
                prefix = "[DIR] " if item.is_dir() else "[FILE]"
                items.append(f"{prefix} {item.name}")
            return "\n".join(items) if items else "(empty directory)"
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    def _get_current_editor(self) -> str:
        """Get content from the current editor."""
        if self.get_editor_content:
            try:
                content = self.get_editor_content()
                if content:
                    return content
                return "(editor is empty or no file open)"
            except Exception as e:
                return f"Error getting editor content: {str(e)}"
        return "(editor access not available)"

    def _search_files(self, pattern: str, file_pattern: str = "*") -> str:
        """Search for files containing a pattern."""
        results = []
        root = Path(self.project_root)

        try:
            for file_path in root.rglob(file_pattern):
                if file_path.is_file() and not any(p.startswith('.') for p in file_path.parts):
                    try:
                        content = file_path.read_text(errors='replace')
                        if pattern.lower() in content.lower():
                            rel_path = file_path.relative_to(root)
                            results.append(str(rel_path))
                            if len(results) >= 20:
                                results.append("... (more results truncated)")
                                break
                    except Exception:
                        pass
            return "\n".join(results) if results else "No matches found"
        except Exception as e:
            return f"Error searching: {str(e)}"

    def get_system_prompt(self) -> str:
        """Get the system prompt."""
        return f"""You are an AI coding assistant integrated into a text editor. You have access to the project at: {self.project_root}

You can use tools to:
- Read files from the project
- List directory contents
- Get the current editor content
- Search for patterns in files

Be concise and helpful. When discussing code, reference specific files and line numbers when possible."""


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    name = "openai"
    display_name = "OpenAI GPT-4"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize the OpenAI client."""
        config = get_ai_config()
        api_key = config.get_api_key("openai")
        if api_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=api_key)
            except ImportError:
                logging.warning("openai package not installed")
        else:
            logging.warning("OpenAI API key not set")

    def is_available(self) -> bool:
        return self.client is not None

    def get_tools(self):
        """Get OpenAI-formatted tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file from the project",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path relative to project root"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List files and directories in a path",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path relative to project root"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_editor",
                    "description": "Get the content of the currently open file in the editor",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_files",
                    "description": "Search for files containing a pattern",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Text pattern to search for"
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "Glob pattern for files to search"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            }
        ]

    async def send_message(self, user_message: str, on_chunk: Callable[[str], None] = None) -> str:
        """Send a message to OpenAI."""
        if not self.client:
            return "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."

        self.messages.append({"role": "user", "content": user_message})

        try:
            return await self._get_response(on_chunk)
        except Exception as e:
            error_msg = f"OpenAI Error: {str(e)}"
            logging.error(error_msg)
            return error_msg

    async def _get_response(self, on_chunk: Callable[[str], None] = None) -> str:
        """Get response from OpenAI, handling tool use."""
        import asyncio

        max_iterations = 10
        iteration = 0

        messages_for_api = [{"role": "system", "content": self.get_system_prompt()}] + self.messages

        while iteration < max_iterations:
            iteration += 1

            if on_chunk:
                # Streaming - run entire stream processing in thread
                def process_stream():
                    response_text = ""
                    tool_calls = []

                    stream = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages_for_api,
                        tools=self.get_tools(),
                        stream=True
                    )

                    for chunk in stream:
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta
                        if delta:
                            if delta.content:
                                response_text += delta.content
                                on_chunk(delta.content)
                            if delta.tool_calls:
                                for tc in delta.tool_calls:
                                    if tc.index is not None:
                                        while len(tool_calls) <= tc.index:
                                            tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                                        if tc.id:
                                            tool_calls[tc.index]["id"] = tc.id
                                        if tc.function:
                                            if tc.function.name:
                                                tool_calls[tc.index]["function"]["name"] = tc.function.name
                                            if tc.function.arguments:
                                                tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

                    # Filter out empty tool calls
                    valid_tool_calls = [tc for tc in tool_calls if tc["id"] and tc["function"]["name"]]
                    return response_text, valid_tool_calls

                response_text, tool_calls = await asyncio.to_thread(process_stream)
            else:
                response = await asyncio.to_thread(
                    lambda: self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages_for_api,
                        tools=self.get_tools()
                    )
                )
                message = response.choices[0].message
                response_text = message.content or ""
                tool_calls = [{"id": tc.id, "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in (message.tool_calls or [])]
                finish_reason = response.choices[0].finish_reason

            if tool_calls:
                # Handle tool calls
                messages_for_api.append({
                    "role": "assistant",
                    "content": response_text,
                    "tool_calls": [{"id": tc["id"], "type": "function", "function": tc["function"]} for tc in tool_calls]
                })

                for tc in tool_calls:
                    import json
                    if on_chunk:
                        on_chunk(f"\n[Using {tc['function']['name']}...]\n")
                    try:
                        args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                    except json.JSONDecodeError:
                        args = {}
                    result = self.execute_tool(tc["function"]["name"], args)
                    messages_for_api.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result
                    })
            else:
                self.messages.append({"role": "assistant", "content": response_text})
                return response_text

        return "Max iterations reached"

    async def send_completion(self, prompt: str) -> str:
        """Send a stateless completion request for inline completions."""
        if not self.client:
            return ""

        import asyncio

        try:
            response = await asyncio.to_thread(
                lambda: self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=256
                )
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logging.error(f"OpenAI completion error: {e}")
            return ""


class ClaudeProvider(AIProvider):
    """Anthropic Claude provider."""

    name = "claude"
    display_name = "Claude Sonnet"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize the Anthropic client."""
        config = get_ai_config()
        api_key = config.get_api_key("claude")
        if api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                logging.warning("anthropic package not installed")
        else:
            logging.warning("Claude API key not set")

    def is_available(self) -> bool:
        return self.client is not None

    def get_tools(self):
        """Get Claude-formatted tools."""
        return [
            {
                "name": "read_file",
                "description": "Read the contents of a file from the project",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path relative to project root"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "list_files",
                "description": "List files and directories in a path",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path relative to project root"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "get_current_editor",
                "description": "Get the content of the currently open file in the editor",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "search_files",
                "description": "Search for files containing a pattern",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Text pattern to search for"
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "Glob pattern for files to search"
                        }
                    },
                    "required": ["pattern"]
                }
            }
        ]

    async def send_message(self, user_message: str, on_chunk: Callable[[str], None] = None) -> str:
        """Send a message to Claude."""
        if not self.client:
            return "Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable."

        self.messages.append({"role": "user", "content": user_message})

        try:
            return await self._get_response(on_chunk)
        except Exception as e:
            error_msg = f"Claude Error: {str(e)}"
            logging.error(error_msg)
            return error_msg

    async def _get_response(self, on_chunk: Callable[[str], None] = None) -> str:
        """Get response from Claude, handling tool use."""
        import asyncio

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            if on_chunk:
                response = await self._stream_response(on_chunk)
            else:
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system=self.get_system_prompt(),
                    tools=self.get_tools(),
                    messages=self.messages
                )

            if response.stop_reason == "tool_use":
                assistant_content = response.content
                self.messages.append({"role": "assistant", "content": assistant_content})

                tool_results = []
                for block in assistant_content:
                    if block.type == "tool_use":
                        if on_chunk:
                            on_chunk(f"\n[Using {block.name}...]\n")
                        result = self.execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                self.messages.append({"role": "user", "content": tool_results})
            else:
                text_content = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        text_content += block.text

                self.messages.append({"role": "assistant", "content": response.content})
                return text_content

        return "Max iterations reached"

    async def _stream_response(self, on_chunk: Callable[[str], None]):
        """Stream response from Claude."""
        with self.client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.get_system_prompt(),
            tools=self.get_tools(),
            messages=self.messages
        ) as stream:
            for text in stream.text_stream:
                on_chunk(text)
            return stream.get_final_message()

    async def send_completion(self, prompt: str) -> str:
        """Send a stateless completion request for inline completions."""
        if not self.client:
            return ""

        import asyncio

        try:
            response = await asyncio.to_thread(
                lambda: self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            if response.content and hasattr(response.content[0], 'text'):
                return response.content[0].text
            return ""
        except Exception as e:
            logging.error(f"Claude completion error: {e}")
            return ""


# Registry of available providers
PROVIDERS = {
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
}

DEFAULT_PROVIDER = "openai"


class AIChat:
    """AI Chat manager that supports multiple providers."""

    def __init__(self, project_root: str, get_editor_content: Callable[[], str] = None):
        self.project_root = project_root
        self.get_editor_content = get_editor_content
        # Get default provider from config
        config = get_ai_config()
        self.current_provider_name = config.get_default_provider()
        if self.current_provider_name not in PROVIDERS:
            self.current_provider_name = DEFAULT_PROVIDER
        self.provider = self._create_provider(self.current_provider_name)

    def _create_provider(self, provider_name: str) -> AIProvider:
        """Create a provider instance."""
        provider_class = PROVIDERS.get(provider_name, PROVIDERS[DEFAULT_PROVIDER])
        return provider_class(
            project_root=self.project_root,
            get_editor_content=self.get_editor_content
        )

    def switch_provider(self, provider_name: str) -> bool:
        """Switch to a different provider."""
        if provider_name not in PROVIDERS:
            return False
        self.current_provider_name = provider_name
        self.provider = self._create_provider(provider_name)
        return True

    def get_available_providers(self) -> List[tuple]:
        """Get list of (name, display_name, is_available) for all providers."""
        result = []
        for name, provider_class in PROVIDERS.items():
            provider = provider_class(self.project_root, self.get_editor_content)
            result.append((name, provider.display_name, provider.is_available()))
        return result

    def get_current_provider_name(self) -> str:
        """Get the current provider name."""
        return self.current_provider_name

    def get_current_display_name(self) -> str:
        """Get the current provider display name."""
        return self.provider.display_name

    def is_available(self) -> bool:
        """Check if the current provider is available."""
        return self.provider.is_available()

    async def send_message(self, user_message: str, on_chunk: Callable[[str], None] = None) -> str:
        """Send a message using the current provider."""
        return await self.provider.send_message(user_message, on_chunk)

    async def send_completion(self, prompt: str) -> str:
        """Send a stateless completion request (no history, no tools)."""
        return await self.provider.send_completion(prompt)

    def clear_history(self):
        """Clear conversation history."""
        self.provider.clear_history()
