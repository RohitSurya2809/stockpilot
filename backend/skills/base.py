"""
Skill Base Class

Skills are business capabilities that orchestrate multiple Tools.
They represent the "how to accomplish a goal" layer.

Examples:
- DemandAnalysisSkill: Orchestrates pattern analysis, forecasting
- RiskAssessmentSkill: Orchestrates risk calculation, threshold checks
- ProcurementSkill: Orchestrates order generation, approval workflow
"""

from typing import Any, Dict, List, Optional, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime

from tools.base import Tool


class SkillInput(BaseModel):
    """Base class for skill inputs"""
    pass


class SkillOutput(BaseModel):
    """Base class for skill outputs"""
    success: bool = Field(description="Whether the skill execution succeeded")
    result: Optional[Any] = Field(default=None, description="Skill result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    tools_used: List[str] = Field(default_factory=list, description="List of tools used")
    execution_time_ms: Optional[float] = Field(default=None, description="Total execution time")


class Skill(ABC):
    """
    Base Skill class

    A Skill:
    - Orchestrates multiple Tools
    - Implements business logic
    - Has typed input/output
    - Tracks which tools were used
    """

    def __init__(self):
        self.name = self.__class__.__name__
        self.description = self.__class__.__doc__ or "No description"
        self.version = "1.0.0"
        self.tools_used: List[str] = []

    @property
    @abstractmethod
    def input_schema(self) -> Type[SkillInput]:
        """Return the input schema for this skill"""
        pass

    @property
    @abstractmethod
    def output_schema(self) -> Type[SkillOutput]:
        """Return the output schema for this skill"""
        pass

    @abstractmethod
    def _execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Internal execution logic (implemented by subclasses)

        Args:
            input_data: Validated input data

        Returns:
            SkillOutput with results
        """
        pass

    def execute(self, **kwargs) -> SkillOutput:
        """
        Execute the skill with validation

        Args:
            **kwargs: Input parameters

        Returns:
            SkillOutput with results
        """
        start_time = datetime.utcnow()
        self.tools_used = []

        try:
            # Validate input
            input_data = self.input_schema(**kwargs)

            # Execute
            result = self._execute(input_data)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            result.tools_used = self.tools_used

            return result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return self.output_schema(
                success=False,
                error=str(e),
                tools_used=self.tools_used,
                execution_time_ms=execution_time
            )

    def use_tool(self, tool: Tool, **kwargs) -> Any:
        """
        Use a tool and track it

        Args:
            tool: Tool instance
            **kwargs: Tool input parameters

        Returns:
            Tool output
        """
        self.tools_used.append(tool.name)
        return tool.execute(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Return skill metadata"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "input_schema": self.input_schema.schema(),
            "output_schema": self.output_schema.schema()
        }


class SkillRegistry:
    """
    Registry for all available skills
    """

    def __init__(self):
        self._skills: Dict[str, Type[Skill]] = {}

    def register(self, skill_class: Type[Skill]):
        """Register a skill class"""
        skill_instance = skill_class()
        self._skills[skill_instance.name] = skill_class

    def get(self, skill_name: str) -> Optional[Skill]:
        """Get a skill instance by name"""
        skill_class = self._skills.get(skill_name)
        if skill_class:
            return skill_class()
        return None

    def list_skills(self) -> Dict[str, Dict[str, Any]]:
        """List all registered skills with metadata"""
        return {
            name: skill_class().to_dict()
            for name, skill_class in self._skills.items()
        }


# Global skill registry
skill_registry = SkillRegistry()
