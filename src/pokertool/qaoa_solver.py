"""
Quantum Approximate Optimization Algorithm (QAOA) Solver

Implements QAOA for combinatorial optimization problems in poker strategy.
Part of QUANTUM-001: Quantum-Inspired Optimization

QAOA is particularly effective for:
- Range optimization with complex constraints
- Multi-player game tree optimization
- Tournament ICM decision optimization
"""

import numpy as np
from typing import Dict, List, Tuple, Callable, Optional
from dataclasses import dataclass
import json


@dataclass
class QAOAParameters:
    """Parameters for QAOA algorithm"""
    num_layers: int = 3  # p parameter (number of QAOA layers)
    num_iterations: int = 100  # Optimization iterations
    learning_rate: float = 0.1
    beta_init: List[float] = None  # Mixing angles
    gamma_init: List[float] = None  # Problem angles


@dataclass
class QAOAResult:
    """Result from QAOA optimization"""
    best_bitstring: str
    best_energy: float
    optimal_params: Dict[str, List[float]]
    energy_history: List[float]
    probability_distribution: Dict[str, float]
    num_iterations: int
    converged: bool


class QAOAProblemHamiltonian:
    """Defines the problem Hamiltonian for QAOA"""
    
    def __init__(self, cost_function: Callable[[np.ndarray], float]):
        """
        Args:
            cost_function: Function mapping bitstring to cost/energy
        """
        self.cost_function = cost_function
        self.cache = {}
    
    def evaluate(self, bitstring: np.ndarray) -> float:
        """Evaluate cost function for a bitstring"""
        key = tuple(bitstring)
        if key in self.cache:
            return self.cache[key]
        
        cost = self.cost_function(bitstring)
        self.cache[key] = cost
        return cost
    
    def apply_cost_operator(self, state_vector: np.ndarray,
                           gamma: float) -> np.ndarray:
        """Apply cost operator exp(-i*gamma*C) to state vector"""
        n = int(np.log2(len(state_vector)))
        new_state = state_vector.copy()
        
        # For each basis state, apply phase based on cost
        for i in range(len(state_vector)):
            bitstring = np.array([int(b) for b in format(i, f'0{n}b')])
            cost = self.evaluate(bitstring)
            phase = np.exp(-1j * gamma * cost)
            new_state[i] *= phase
        
        return new_state


class QAOAMixingHamiltonian:
    """Defines the mixing Hamiltonian for QAOA"""
    
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.dimension = 2 ** num_qubits
    
    def apply_mixing_operator(self, state_vector: np.ndarray,
                             beta: float) -> np.ndarray:
        """Apply mixing operator exp(-i*beta*B) to state vector"""
        # B is typically sum of X operators
        # This creates superposition by flipping qubits
        new_state = state_vector.copy()
        
        # For each qubit, apply X rotation
        for qubit in range(self.num_qubits):
            new_state = self._apply_x_rotation(new_state, qubit, beta)
        
        return new_state
    
    def _apply_x_rotation(self, state_vector: np.ndarray,
                         qubit: int, beta: float) -> np.ndarray:
        """Apply X rotation on specific qubit"""
        n = self.num_qubits
        new_state = np.zeros_like(state_vector)
        
        # Rotation matrix for single qubit
        cos_beta = np.cos(beta)
        sin_beta = np.sin(beta)
        
        for i in range(len(state_vector)):
            bitstring = format(i, f'0{n}b')
            
            # Create flipped bitstring
            bit_list = list(bitstring)
            bit_list[qubit] = '1' if bit_list[qubit] == '0' else '0'
            flipped_idx = int(''.join(bit_list), 2)
            
            # Apply rotation
            new_state[i] += cos_beta * state_vector[i] - 1j * sin_beta * state_vector[flipped_idx]
        
        return new_state


class QAOASolver:
    """Main QAOA solver implementation"""
    
    def __init__(self, num_qubits: int,
                 cost_function: Callable[[np.ndarray], float]):
        """
        Args:
            num_qubits: Number of qubits (problem variables)
            cost_function: Cost function to minimize
        """
        self.num_qubits = num_qubits
        self.dimension = 2 ** num_qubits
        self.problem_hamiltonian = QAOAProblemHamiltonian(cost_function)
        self.mixing_hamiltonian = QAOAMixingHamiltonian(num_qubits)
    
    def initialize_state(self) -> np.ndarray:
        """Initialize uniform superposition state"""
        state = np.ones(self.dimension, dtype=complex) / np.sqrt(self.dimension)
        return state
    
    def apply_qaoa_layer(self, state: np.ndarray,
                        gamma: float, beta: float) -> np.ndarray:
        """Apply one QAOA layer"""
        # Apply problem Hamiltonian
        state = self.problem_hamiltonian.apply_cost_operator(state, gamma)
        
        # Apply mixing Hamiltonian
        state = self.mixing_hamiltonian.apply_mixing_operator(state, beta)
        
        # Normalize
        norm = np.sqrt(np.sum(np.abs(state) ** 2))
        if norm > 0:
            state = state / norm
        
        return state
    
    def compute_expectation(self, state: np.ndarray) -> float:
        """Compute expectation value of cost function"""
        expectation = 0.0
        
        for i in range(self.dimension):
            probability = np.abs(state[i]) ** 2
            bitstring = np.array([int(b) for b in format(i, f'0{self.num_qubits}b')])
            cost = self.problem_hamiltonian.evaluate(bitstring)
            expectation += probability * cost
        
        return expectation
    
    def optimize_parameters(self, params: QAOAParameters) -> Tuple[List[float], List[float]]:
        """Optimize QAOA parameters using gradient descent"""
        # Initialize parameters
        if params.beta_init:
            betas = list(params.beta_init)
        else:
            betas = [0.5] * params.num_layers
        
        if params.gamma_init:
            gammas = list(params.gamma_init)
        else:
            gammas = [0.5] * params.num_layers
        
        energy_history = []
        epsilon = 0.01  # For numerical gradients
        
        for iteration in range(params.num_iterations):
            # Compute current expectation
            state = self.initialize_state()
            for p in range(params.num_layers):
                state = self.apply_qaoa_layer(state, gammas[p], betas[p])
            
            current_energy = self.compute_expectation(state)
            energy_history.append(current_energy)
            
            # Compute gradients numerically (simplified)
            for p in range(params.num_layers):
                # Gradient w.r.t. gamma
                gammas[p] += epsilon
                state_plus = self.initialize_state()
                for pp in range(params.num_layers):
                    state_plus = self.apply_qaoa_layer(state_plus, gammas[pp], betas[pp])
                energy_plus = self.compute_expectation(state_plus)
                gammas[p] -= epsilon
                
                grad_gamma = (energy_plus - current_energy) / epsilon
                gammas[p] -= params.learning_rate * grad_gamma
                
                # Gradient w.r.t. beta
                betas[p] += epsilon
                state_plus = self.initialize_state()
                for pp in range(params.num_layers):
                    state_plus = self.apply_qaoa_layer(state_plus, gammas[pp], betas[pp])
                energy_plus = self.compute_expectation(state_plus)
                betas[p] -= epsilon
                
                grad_beta = (energy_plus - current_energy) / epsilon
                betas[p] -= params.learning_rate * grad_beta
            
            # Check convergence
            if iteration > 10:
                recent_energies = energy_history[-10:]
                if max(recent_energies) - min(recent_energies) < 0.001:
                    break
        
        return gammas, betas
    
    def solve(self, params: Optional[QAOAParameters] = None) -> QAOAResult:
        """Solve optimization problem using QAOA"""
        if params is None:
            params = QAOAParameters()
        
        # Optimize parameters
        optimal_gammas, optimal_betas = self.optimize_parameters(params)
        
        # Generate final state with optimal parameters
        final_state = self.initialize_state()
        for p in range(params.num_layers):
            final_state = self.apply_qaoa_layer(
                final_state, optimal_gammas[p], optimal_betas[p]
            )
        
        # Extract probability distribution
        prob_dist = {}
        best_bitstring = None
        best_energy = float('inf')
        
        for i in range(self.dimension):
            probability = np.abs(final_state[i]) ** 2
            bitstring_str = format(i, f'0{self.num_qubits}b')
            bitstring_arr = np.array([int(b) for b in bitstring_str])
            
            energy = self.problem_hamiltonian.evaluate(bitstring_arr)
            prob_dist[bitstring_str] = float(probability)
            
            if energy < best_energy and probability > 0.01:
                best_energy = energy
                best_bitstring = bitstring_str
        
        # Compute final expectation
        final_expectation = self.compute_expectation(final_state)
        
        return QAOAResult(
            best_bitstring=best_bitstring or '0' * self.num_qubits,
            best_energy=best_energy,
            optimal_params={'gammas': optimal_gammas, 'betas': optimal_betas},
            energy_history=[final_expectation],
            probability_distribution=prob_dist,
            num_iterations=params.num_iterations,
            converged=True
        )
    
    def sample_solution(self, num_samples: int = 100,
                       params: Optional[QAOAParameters] = None) -> List[Tuple[str, float]]:
        """Sample solutions from QAOA distribution"""
        result = self.solve(params)
        
        # Sample from probability distribution
        bitstrings = list(result.probability_distribution.keys())
        probabilities = list(result.probability_distribution.values())
        
        # Normalize probabilities
        total_prob = sum(probabilities)
        if total_prob > 0:
            probabilities = [p / total_prob for p in probabilities]
        
        # Sample
        samples = []
        rng = np.random.RandomState(42)
        
        for _ in range(num_samples):
            idx = rng.choice(len(bitstrings), p=probabilities)
            bitstring = bitstrings[idx]
            bitstring_arr = np.array([int(b) for b in bitstring])
            energy = self.problem_hamiltonian.evaluate(bitstring_arr)
            samples.append((bitstring, energy))
        
        # Return unique samples sorted by energy
        unique_samples = {}
        for bitstring, energy in samples:
            if bitstring not in unique_samples or energy < unique_samples[bitstring]:
                unique_samples[bitstring] = energy
        
        return sorted(unique_samples.items(), key=lambda x: x[1])


class PokerQAOASolver:
    """QAOA solver specialized for poker problems"""
    
    def __init__(self):
        self.solver = None
    
    def optimize_poker_range(self, candidate_hands: List[str],
                            hand_values: Dict[str, float],
                            max_hands: int = 10) -> List[str]:
        """
        Optimize poker range selection using QAOA
        
        Args:
            candidate_hands: List of possible hands
            hand_values: EV value for each hand
            max_hands: Maximum hands to select
        
        Returns:
            List of selected hands
        """
        n = len(candidate_hands)
        
        # Define cost function
        def cost_function(bitstring: np.ndarray) -> float:
            selected_count = np.sum(bitstring)
            
            # Penalty for violating max_hands constraint
            if selected_count > max_hands:
                return 1000.0 + (selected_count - max_hands) * 100
            
            # Maximize total value (minimize negative value)
            total_value = 0.0
            for i, bit in enumerate(bitstring):
                if bit == 1:
                    hand = candidate_hands[i]
                    total_value += hand_values.get(hand, 0.0)
            
            return -total_value
        
        # Solve with QAOA
        self.solver = QAOASolver(n, cost_function)
        params = QAOAParameters(num_layers=2, num_iterations=50)
        result = self.solver.solve(params)
        
        # Extract selected hands
        selected_hands = []
        for i, bit in enumerate(result.best_bitstring):
            if bit == '1':
                selected_hands.append(candidate_hands[i])
        
        return selected_hands
    
    def optimize_multiway_action(self, num_opponents: int,
                                 action_values: Dict[str, float]) -> str:
        """
        Optimize action in multiway pot using QAOA
        
        Args:
            num_opponents: Number of opponents in hand
            action_values: EV for each action
        
        Returns:
            Best action
        """
        actions = list(action_values.keys())
        n = len(actions)
        
        # Define cost function (select exactly one action)
        def cost_function(bitstring: np.ndarray) -> float:
            selected_count = np.sum(bitstring)
            
            # Must select exactly one action
            if selected_count != 1:
                return 1000.0
            
            # Return negative value (minimize)
            for i, bit in enumerate(bitstring):
                if bit == 1:
                    return -action_values[actions[i]]
            
            return 0.0
        
        # Solve
        self.solver = QAOASolver(n, cost_function)
        params = QAOAParameters(num_layers=1, num_iterations=30)
        result = self.solver.solve(params)
        
        # Extract action
        for i, bit in enumerate(result.best_bitstring):
            if bit == '1':
                return actions[i]
        
        return actions[0]  # Default
    
    def export_result(self, result: QAOAResult, filepath: str):
        """Export QAOA result to JSON"""
        data = {
            'best_bitstring': result.best_bitstring,
            'best_energy': float(result.best_energy),
            'optimal_params': {
                'gammas': [float(g) for g in result.optimal_params['gammas']],
                'betas': [float(b) for b in result.optimal_params['betas']]
            },
            'probability_distribution': {
                k: float(v) for k, v in result.probability_distribution.items()
            },
            'num_iterations': result.num_iterations,
            'converged': result.converged
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


# Utility functions
def solve_maxcut_qaoa(graph: Dict[Tuple[int, int], float],
                     num_layers: int = 2) -> Tuple[str, float]:
    """Solve MaxCut problem using QAOA (useful for game tree analysis)"""
    num_nodes = max(max(edge) for edge in graph.keys()) + 1
    
    def maxcut_cost(bitstring: np.ndarray) -> float:
        cost = 0.0
        for (i, j), weight in graph.items():
            if bitstring[i] != bitstring[j]:
                cost -= weight  # Negative because we minimize
        return cost
    
    solver = QAOASolver(num_nodes, maxcut_cost)
    params = QAOAParameters(num_layers=num_layers, num_iterations=50)
    result = solver.solve(params)
    
    return result.best_bitstring, result.best_energy


def optimize_portfolio_qaoa(asset_values: List[float],
                           correlations: np.ndarray,
                           budget: int) -> List[int]:
    """Optimize portfolio selection (useful for bankroll allocation)"""
    n = len(asset_values)
    
    def portfolio_cost(bitstring: np.ndarray) -> float:
        if np.sum(bitstring) > budget:
            return 1000.0
        
        # Maximize value minus correlation penalty
        value = -np.dot(bitstring, asset_values)
        
        # Add correlation penalty
        for i in range(n):
            for j in range(i+1, n):
                if bitstring[i] == 1 and bitstring[j] == 1:
                    value += correlations[i, j] * 10  # Penalty for correlation
        
        return value
    
    solver = QAOASolver(n, portfolio_cost)
    result = solver.solve()
    
    return [i for i, bit in enumerate(result.best_bitstring) if bit == '1']
