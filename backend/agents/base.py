"""
Agent Base Class

Agents are autonomous decision-makers that orchestrate Skills.
They represent the "what to do and when" layer.

Examples:
- InventoryAgent: Decides when to analyze, when to reorder, what to escalate
"""

from typing import Any, Dict, List, Optional, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from skills.base import Skill


class AgentDecisionType(str, Enum):
    """Types of decisions an agent can make"""
    ANALYZE = "analyze"
    REORDER = "reorder"
    ESCALATE = "escalate"
    MONITOR = "monitor"
    APPROVE = "approve"
    REJECT = "reject"


class AgentInput(BaseModel):
    """Base class for agent inputs"""
    pass


class AgentOutput(BaseModel):
    """Base class for agent outputs"""
    success: bool = Field(description="Whether the agent execution succeeded")
    decision: Optional[str] = Field(default=None, description="Decision made by agent")
    decision_type: Optional[AgentDecisionType] = Field(default=None, description="Type of decision")
    reasoning: Optional[str] = Field(default=None, description="Explanation of decision")
    actions_taken: List[str] = Field(default_factory=list, description="Actions performed")
    skills_used: List[str] = Field(default_factory=list, description="Skills used")
    result_data: Optional[Any] = Field(default=None, description="Result data")
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence in decision")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_ms: Optional[float] = Field(default=None, description="Total execution time")


class Agent(ABC):
    """
    Base Agent class

    An Agent:
    - Makes decisions about what to do
    - Orchestrates Skills to gather information
    - Produces actionable outputs with reasoning
    - Logs all decisions for audit trail
    """

    def __init__(self, db_session=None):
        self.name = self.__class__.__name__
        self.description = self.__class__.__doc__ or "No description"
        self.version = "1.0.0"
        self.db_session = db_session
        self.skills_used: List[str] = []
        self.actions_taken: List[str] = []

    @property
    @abstractmethod
    def input_schema(self) -> Type[AgentInput]:
        """Return the input schema for this agent"""
        pass

    @property
    @abstractmethod
    def output_schema(self) -> Type[AgentOutput]:
        """Return the output schema for this agent"""
        pass

    @abstractmethod
    def _execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Internal execution logic (implemented by subclasses)

        This is where the agent's intelligence lives:
        - Gather information using skills
        - Analyze the situation
        - Make a decision
        - Take action

        Args:
            input_data: Validated input data

        Returns:
            AgentOutput with decision and results
        """
        pass

    def execute(self, **kwargs) -> AgentOutput:
        """
        Execute the agent with validation and logging

        Args:
            **kwargs: Input parameters

        Returns:
            AgentOutput with decision and results
        """
        start_time = datetime.utcnow()
        self.skills_used = []
        self.actions_taken = []

        try:
            # Validate input
            input_data = self.input_schema(**kwargs)

            # Execute
            result = self._execute(input_data)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            result.skills_used = self.skills_used
            result.actions_taken = self.actions_taken

            # Log decision (if database available)
            if self.db_session and result.success:
                self._log_decision(input_data, result)

            return result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            error_result = self.output_schema(
                success=False,
                error=str(e),
                skills_used=self.skills_used,
                actions_taken=self.actions_taken,
                execution_time_ms=execution_time
            )

            # Log error
            if self.db_session:
                self._log_decision(input_data, error_result)

            return error_result

    def use_skill(self, skill: Skill, **kwargs) -> Any:
        """
        Use a skill and track it

        Args:
            skill: Skill instance
            **kwargs: Skill input parameters

        Returns:
            Skill output
        """
        self.skills_used.append(skill.name)
        return skill.execute(**kwargs)

    def log_action(self, action: str):
        """
        Log an action taken by the agent

        Args:
            action: Description of action
        """
        self.actions_taken.append(action)

    def _log_decision(self, input_data: AgentInput, output_data: AgentOutput):
        """
        Log agent decision to database

        Args:
            input_data: Input that led to decision
            output_data: Decision output
        """
        try:
            from models import AgentLog
            import json

            log_entry = AgentLog(
                agent_id=self.name,
                decision_type=output_data.decision_type.value if output_data.decision_type else "unknown",
                reasoning=output_data.reasoning or "No reasoning provided",
                decision_data=output_data.dict()
            )

            self.db_session.add(log_entry)
            self.db_session.commit()

        except Exception as e:
            # Don't fail the agent execution if logging fails
            print(f"Warning: Failed to log agent decision: {str(e)}")

    def to_dict(self) -> Dict[str, Any]:
        """Return agent metadata"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "input_schema": self.input_schema.schema(),
            "output_schema": self.output_schema.schema()
        }


class AgentRegistry:
    """
    Registry for all available agents
    """

    def __init__(self):
        self._agents: Dict[str, Type[Agent]] = {}

    def register(self, agent_class: Type[Agent]):
        """Register an agent class"""
        agent_instance = agent_class()
        self._agents[agent_instance.name] = agent_class

    def get(self, agent_name: str, db_session=None) -> Optional[Agent]:
        """Get an agent instance by name"""
        agent_class = self._agents.get(agent_name)
        if agent_class:
            return agent_class(db_session=db_session)
        return None

    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all registered agents with metadata"""
        return {
            name: agent_class().to_dict()
            for name, agent_class in self._agents.items()
        }


# Global agent registry
agent_registry = AgentRegistry()
