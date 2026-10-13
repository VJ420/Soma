"""
Core Abstractions and Interfaces for Fractal Execution Engines.
Enforces SOLID, Inversion of Control (IoC), and Strategy patterns.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ast_nodes import ProgramNode, ASTNode
from config.settings import RuntimeConfig
from telemetry.logger import TelemetryLogger, MetricsCollector

class IExecutionStrategy(ABC):
    """Strategy interface for plug-and-play execution backends."""
    
    @abstractmethod
    def execute_ast(self, program: ProgramNode, context: Dict[str, Any]) -> Any:
        """Executes an AST representation of Fractal code."""
        pass

    @abstractmethod
    def name(self) -> str:
        """Identifier of the execution engine."""
        pass

class IScopeManager(ABC):
    """Interface for lexical and dynamic Cell scopes."""
    
    @abstractmethod
    def resolve(self, name: str) -> Any:
        pass

    @abstractmethod
    def bind(self, name: str, value: Any) -> None:
        pass

    @abstractmethod
    def create_child_scope(self) -> 'IScopeManager':
        pass

class ICellInvoker(ABC):
    """Interface for Universal Cell invocation."""
    
    @abstractmethod
    def invoke(self, callee: Any, args: List[Any], context: Dict[str, Any]) -> Any:
        pass
