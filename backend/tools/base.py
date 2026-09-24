"""
Tool Base Class

Tools are atomic, typed operations that interact with the system.
They represent the "what can be done" layer.

Examples:
- GetInventoryTool: Fetch inventory data
- CalculateForecastTool: Run forecasting algorithm
- CreatePurchaseOrderTool: Create PO in database
"""

from typing import Any, Dict, Optional, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime


class ToolInput(BaseModel):
    """Base class for tool inputs (strongly typed)"""
    pass


class ToolOutput(BaseModel):
    """Base class for tool outputs (strongly typed)"""
    success: bool = Field(description="Whether the tool execution succeeded")
    data: Optional[Any] = Field(default=None, description="Tool output data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")


class Tool(ABC):
    """
    Base Tool class

    A Tool is a single, atomic operation with:
    - Typed input (Pydantic model)
    - Typed output (Pydantic model)
    - Execute method
    - Metadata (name, description, version)
    """

    def __init__(self):
        self.name = self.__class__.__name__
        self.description = self.__class__.__doc__ or "No description"
        self.version = "1.0.0"

    @property
    @abstractmethod
    def input_schema(self) -> Type[ToolInput]:
        """Return the input schema for this tool"""
        pass

    @property
    @abstractmethod
    def output_schema(self) -> Type[ToolOutput]:
        """Return the output schema for this tool"""
        pass

    @abstractmethod
    def _execute(self, input_data: ToolInput) -> ToolOutput:
        """
        Internal execution logic (implemented by subclasses)

        Args:
            input_data: Validated input data

        Returns:
            ToolOutput with results
        """
        pass

    def execute(self, **kwargs) -> ToolOutput:
        """
        Execute the tool with validation

        Args:
            **kwargs: Input parameters

        Returns:
            ToolOutput with results
        """
        start_time = datetime.utcnow()

        try:
            # Validate input
            input_data = self.input_schema(**kwargs)

            # Execute
            result = self._execute(input_data)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time

            return result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return self.output_schema(
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )

    def to_dict(self) -> Dict[str, Any]:
        """Return tool metadata"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "input_schema": self.input_schema.schema(),
            "output_schema": self.output_schema.schema()
        }


class ToolRegistry:
    """
    Registry for all available tools

    Allows discovery and instantiation of tools by name
    """

    def __init__(self):
        self._tools: Dict[str, Type[Tool]] = {}

    def register(self, tool_class: Type[Tool]):
        """Register a tool class"""
        tool_instance = tool_class()
        self._tools[tool_instance.name] = tool_class

    def get(self, tool_name: str) -> Optional[Tool]:
        """Get a tool instance by name"""
        tool_class = self._tools.get(tool_name)
        if tool_class:
            return tool_class()
        return None

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all registered tools with metadata"""
        return {
            name: tool_class().to_dict()
            for name, tool_class in self._tools.items()
        }


# Global tool registry
tool_registry = ToolRegistry()
