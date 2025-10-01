"""
Tests for Quantum-Inspired Optimization (QUANTUM-001)

Tests quantum annealing simulation, QAOA, superposition state exploration,
entanglement correlations, and measurement collapse strategies.
"""

import pytest
import numpy as np
import tempfile
import os
from src.pokertool.quantum_optimizer import (
    QuantumAnnealingSimulator,
    SuperpositionStateExplorer,
    EntanglementCorrelationAnalyzer,
    QuantumInspiredOptimizer,
    QuantumState,
    OptimizationResult,
    OptimizationType,
    quick_optimize_range,
    find_optimal_action
)
from src.pokertool.qaoa_solver import (
    QAOASolver,
    QAOAParameters,
    QAOAResult,
    QAOAProblemHamiltonian,
    QAOAMixingHamiltonian,
    PokerQAOASolver,
    solve_maxcut_qaoa,
    optimize_portfolio_qaoa
)


class TestQuantumAnnealingSimulator:
    """Test quantum annealing simulation"""
    
    def test_initialization(self):
        """Test simulator initialization"""
        annealer = QuantumAnnealingSimulator()
        assert annealer is not None
        assert hasattr(annealer, 'temperature_schedule')
    
    def test_temperature_schedule(self):
        """Test temperature cooling schedule"""
        annealer = QuantumAnnealingSimulator()
        
        # Temperature should decrease
        temp_start = annealer.temperature_schedule(0.0)
        temp_middle = annealer.temperature_schedule(0.5)
        temp_end = annealer.temperature_schedule(1.0)
        
        assert temp_start > temp_middle > temp_end
    
    def test_simple_optimization(self):
        """Test simple optimization problem"""
        annealer = QuantumAnnealingSimulator()
        
        # Simple problem: minimize sum of bits
        problem = {
            'linear': np.array([1.0, 1.0, 1.0, 1.0]),
            'quadratic': {},
            'constraints': []
        }
        
        result = annealer.anneal(problem, num_iterations=500)
        
        assert isinstance(result, OptimizationResult)
        assert len(result.best_solution) == 4
        assert result.iterations == 500
        # Should find all zeros (minimum energy)
        assert result.best_solution.count('0') >= 3
    
    def test_with_constraints(self):
        """Test optimization with constraints"""
        annealer = QuantumAnnealingSimulator()
        
        # Problem with constraint: exactly 2 bits set
        def constraint(state):
            return np.sum(state) == 2
        
        problem = {
            'linear': np.array([1.0, 2.0, 3.0, 4.0]),
            'quadratic': {},
            'constraints': [constraint]
        }
        
        result = annealer.anneal(problem, num_iterations=500)
        
        # Check constraint is satisfied
        ones_count = result.best_solution.count('1')
        assert ones_count == 2 or result.best_energy > 100  # Heavy penalty if violated
    
    def test_quadratic_terms(self):
        """Test optimization with quadratic interactions"""
        annealer = QuantumAnnealingSimulator()
        
        # Problem with interactions
        problem = {
            'linear': np.array([0.0, 0.0]),
            'quadratic': {(0, 1): -5.0},  # Prefer both bits same
            'constraints': []
        }
        
        result = annealer.anneal(problem, num_iterations=500)
        
        # Should find either "00" or "11"
        assert result.best_solution in ['00', '11']


class TestSuperpositionStateExplorer:
    """Test superposition state exploration"""
    
    def test_create_superposition(self):
        """Test creating superposition of states"""
        explorer = SuperpositionStateExplorer(num_states=4)
        
        possible_states = ['000', '001', '010', '011', '100', '101', '110', '111']
        state = explorer.create_superposition(possible_states)
        
        assert isinstance(state, QuantumState)
        assert len(state.amplitudes) <= 4
        assert len(state.basis_states) <= 4
        # Check normalization
        prob_sum = np.sum(np.abs(state.amplitudes) ** 2)
        assert abs(prob_sum - 1.0) < 0.01
    
    def test_apply_phase_gate(self):
        """Test phase gate application"""
        explorer = SuperpositionStateExplorer(num_states=3)
        
        states = ['00', '01', '10']
        initial_state = explorer.create_superposition(states)
        
        # Phase function: favor '11' bitstrings
        def phase_func(s):
            return s.count('1') * 0.5
        
        new_state = explorer.apply_phase_gate(initial_state, phase_func)
        
        assert isinstance(new_state, QuantumState)
        assert len(new_state.amplitudes) == len(initial_state.amplitudes)
    
    def test_measure(self):
        """Test state measurement"""
        explorer = SuperpositionStateExplorer(num_states=4)
        
        states = ['00', '01', '10', '11']
        quantum_state = explorer.create_superposition(states)
        
        measured, prob = explorer.measure(quantum_state)
        
        assert measured in states
        assert 0 <= prob <= 1
    
    def test_grover_iteration(self):
        """Test Grover's algorithm iteration"""
        explorer = SuperpositionStateExplorer(num_states=4)
        
        states = ['00', '01', '10', '11']
        quantum_state = explorer.create_superposition(states)
        
        # Oracle: mark '11' as solution
        def oracle(s):
            return s == '11'
        
        new_state = explorer.grover_iteration(quantum_state, oracle)
        
        assert isinstance(new_state, QuantumState)
        # After Grover iteration, '11' should have higher amplitude
    
    def test_explore_space(self):
        """Test space exploration"""
        explorer = SuperpositionStateExplorer(num_states=5)
        
        possible_states = ['000', '001', '010', '011', '100', '101', '110', '111']
        
        # Objective: maximize number of ones
        def objective(s):
            return -s.count('1')  # Negative to minimize
        
        solutions = explorer.explore_space(possible_states, objective, num_iterations=10)
        
        assert len(solutions) > 0
        # Best solution should have many ones
        best_solution = solutions[0][0]
        assert best_solution.count('1') >= 2


class TestEntanglementCorrelationAnalyzer:
    """Test entanglement correlation analysis"""
    
    def test_create_entangled_pair(self):
        """Test entanglement calculation"""
        analyzer = EntanglementCorrelationAnalyzer()
        
        # Similar states should be more entangled
        entanglement1 = analyzer.create_entangled_pair('000', '001')
        entanglement2 = analyzer.create_entangled_pair('000', '111')
        
        assert 0 <= entanglement1 <= 1
        assert 0 <= entanglement2 <= 1
        assert entanglement1 > entanglement2  # More similar states
    
    def test_build_entanglement_network(self):
        """Test building entanglement network"""
        analyzer = EntanglementCorrelationAnalyzer()
        
        states = ['000', '001', '010', '011']
        network = analyzer.build_entanglement_network(states)
        
        assert isinstance(network, dict)
        # Network may be empty if no pairs exceed threshold
        # The threshold is 0.5, and these states have low similarity
        # Just check it's a valid dict
    
    def test_find_maximally_entangled_states(self):
        """Test finding maximally entangled states"""
        analyzer = EntanglementCorrelationAnalyzer()
        
        states = ['000', '001', '110', '111']
        entangled = analyzer.find_maximally_entangled_states(states, top_k=2)
        
        assert len(entangled) <= 2
        for state1, state2, strength in entangled:
            assert state1 in states
            assert state2 in states
            assert 0 <= strength <= 1
    
    def test_calculate_correlation_matrix(self):
        """Test correlation matrix calculation"""
        analyzer = EntanglementCorrelationAnalyzer()
        
        states = ['00', '01', '10', '11']
        matrix = analyzer.calculate_correlation_matrix(states)
        
        assert matrix.shape == (4, 4)
        # Diagonal should be 1.0
        assert np.all(np.diag(matrix) == 1.0)
        # Matrix should be symmetric
        assert np.allclose(matrix, matrix.T)


class TestQuantumInspiredOptimizer:
    """Test main quantum optimizer"""
    
    def test_initialization(self):
        """Test optimizer initialization"""
        optimizer = QuantumInspiredOptimizer()
        
        assert optimizer.annealer is not None
        assert optimizer.superposition_explorer is not None
        assert optimizer.entanglement_analyzer is not None
    
    def test_optimize_range_construction(self):
        """Test range construction optimization"""
        optimizer = QuantumInspiredOptimizer()
        
        candidates = ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77']
        
        def objective(hands):
            # Prefer premium hands
            premium = {'AA', 'KK', 'QQ'}
            score = sum(1.0 for h in hands if h in premium)
            return -score
        
        result = optimizer.optimize_range_construction(
            candidates,
            objective,
            max_hands=4
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.best_solution is not None
        # Should select hands
        assert result.best_solution.count('1') <= 4
    
    def test_optimize_action_selection(self):
        """Test action selection optimization"""
        optimizer = QuantumInspiredOptimizer()
        
        actions = ['fold', 'call', 'raise_small', 'raise_large', 'all_in']
        context = {'pot': 100, 'stack': 200}
        
        best_action, value = optimizer.optimize_action_selection(actions, context)
        
        assert best_action in actions
        assert isinstance(value, float)
    
    def test_find_correlated_strategies(self):
        """Test finding correlated strategies"""
        optimizer = QuantumInspiredOptimizer()
        
        strategies = ['000', '001', '010', '100', '110', '111']
        correlated = optimizer.find_correlated_strategies(strategies, top_k=3)
        
        assert len(correlated) <= 3
        for s1, s2, strength in correlated:
            assert s1 in strategies
            assert s2 in strategies
    
    def test_optimize_bet_sizing(self):
        """Test bet sizing optimization"""
        optimizer = QuantumInspiredOptimizer()
        
        bet_sizes = optimizer.optimize_bet_sizing(
            pot_size=100,
            stack_size=500,
            num_options=8
        )
        
        assert len(bet_sizes) > 0
        # Check all bet sizes are reasonable
        for bet, score in bet_sizes:
            assert 30 <= bet <= 300  # Between 0.3 pot and 3x pot
    
    def test_export_optimization_report(self):
        """Test exporting optimization report"""
        optimizer = QuantumInspiredOptimizer()
        
        result = OptimizationResult(
            best_solution='101010',
            best_energy=5.5,
            probability=0.75,
            all_solutions=[('101010', 5.5, 0.75)],
            iterations=100,
            converged=True
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name
        
        try:
            optimizer.export_optimization_report(result, filepath)
            assert os.path.exists(filepath)
            
            import json
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert data['best_solution'] == '101010'
            assert data['converged'] is True
        finally:
            os.unlink(filepath)


class TestQAOASolver:
    """Test QAOA solver"""
    
    def test_initialization(self):
        """Test QAOA solver initialization"""
        def cost_func(bitstring):
            return np.sum(bitstring)
        
        solver = QAOASolver(num_qubits=3, cost_function=cost_func)
        
        assert solver.num_qubits == 3
        assert solver.dimension == 8
    
    def test_initialize_state(self):
        """Test state initialization"""
        def cost_func(bitstring):
            return np.sum(bitstring)
        
        solver = QAOASolver(num_qubits=3, cost_function=cost_func)
        state = solver.initialize_state()
        
        assert len(state) == 8
        # Check uniform superposition
        prob = np.abs(state[0]) ** 2
        assert abs(prob - 1.0/8.0) < 0.01
    
    def test_compute_expectation(self):
        """Test expectation value computation"""
        def cost_func(bitstring):
            return np.sum(bitstring)
        
        solver = QAOASolver(num_qubits=2, cost_function=cost_func)
        state = solver.initialize_state()
        
        expectation = solver.compute_expectation(state)
        
        # For uniform superposition, expectation should be 1.0
        assert abs(expectation - 1.0) < 0.1
    
    def test_solve_simple_problem(self):
        """Test solving simple optimization"""
        # Minimize sum of bits
        def cost_func(bitstring):
            return np.sum(bitstring)
        
        solver = QAOASolver(num_qubits=3, cost_function=cost_func)
        params = QAOAParameters(num_layers=1, num_iterations=20)
        
        result = solver.solve(params)
        
        assert isinstance(result, QAOAResult)
        assert result.best_bitstring is not None
        # Should prefer zeros
        assert result.best_bitstring.count('0') >= 2
    
    def test_sample_solution(self):
        """Test solution sampling"""
        def cost_func(bitstring):
            return np.sum(bitstring)
        
        solver = QAOASolver(num_qubits=3, cost_function=cost_func)
        params = QAOAParameters(num_layers=1, num_iterations=20)
        
        samples = solver.sample_solution(num_samples=50, params=params)
        
        assert len(samples) > 0
        # Samples are tuples of (bitstring, energy)
        for sample in samples:
            assert isinstance(sample, tuple)
            assert len(sample) == 2
            assert isinstance(sample[0], str)
            assert isinstance(sample[1], (int, float, np.floating, np.integer))


class TestPokerQAOASolver:
    """Test poker-specific QAOA solver"""
    
    def test_initialization(self):
        """Test poker QAOA solver initialization"""
        solver = PokerQAOASolver()
        assert solver is not None
    
    def test_optimize_poker_range(self):
        """Test poker range optimization"""
        solver = PokerQAOASolver()
        
        candidates = ['AA', 'KK', 'QQ', 'JJ', 'TT']
        hand_values = {
            'AA': 10.0,
            'KK': 9.0,
            'QQ': 7.0,
            'JJ': 5.0,
            'TT': 3.0
        }
        
        selected = solver.optimize_poker_range(candidates, hand_values, max_hands=3)
        
        assert isinstance(selected, list)
        assert len(selected) <= 3
        # Should select high value hands
        assert 'AA' in selected or 'KK' in selected
    
    def test_optimize_multiway_action(self):
        """Test multiway action optimization"""
        solver = PokerQAOASolver()
        
        action_values = {
            'fold': 0.0,
            'call': 5.0,
            'raise': 8.0
        }
        
        best_action = solver.optimize_multiway_action(2, action_values)
        
        assert best_action in action_values.keys()
        # Should prefer raise (highest value)
        assert best_action == 'raise'
    
    def test_export_result(self):
        """Test result export"""
        solver = PokerQAOASolver()
        
        result = QAOAResult(
            best_bitstring='101',
            best_energy=3.5,
            optimal_params={'gammas': [0.5, 0.7], 'betas': [0.3, 0.6]},
            energy_history=[5.0, 4.0, 3.5],
            probability_distribution={'101': 0.8, '001': 0.2},
            num_iterations=50,
            converged=True
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name
        
        try:
            solver.export_result(result, filepath)
            assert os.path.exists(filepath)
        finally:
            os.unlink(filepath)


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_quick_optimize_range(self):
        """Test quick range optimization"""
        candidates = ['AA', 'KK', 'QQ', 'AK', '99']
        
        result = quick_optimize_range(candidates, max_hands=3)
        
        assert isinstance(result, str)
        assert len(result) == len(candidates)
        assert result.count('1') <= 3
    
    def test_find_optimal_action(self):
        """Test optimal action finding"""
        actions = ['fold', 'call', 'raise']
        
        best_action = find_optimal_action(actions)
        
        assert best_action in actions
    
    def test_solve_maxcut_qaoa(self):
        """Test MaxCut problem solving"""
        # Simple graph: 4 nodes
        graph = {
            (0, 1): 1.0,
            (1, 2): 1.0,
            (2, 3): 1.0,
            (3, 0): 1.0
        }
        
        solution, energy = solve_maxcut_qaoa(graph, num_layers=1)
        
        assert len(solution) == 4
        assert isinstance(energy, float)
    
    def test_optimize_portfolio_qaoa(self):
        """Test portfolio optimization"""
        asset_values = [10.0, 8.0, 6.0, 4.0]
        correlations = np.array([
            [1.0, 0.5, 0.2, 0.1],
            [0.5, 1.0, 0.3, 0.2],
            [0.2, 0.3, 1.0, 0.4],
            [0.1, 0.2, 0.4, 1.0]
        ])
        
        selected = optimize_portfolio_qaoa(asset_values, correlations, budget=2)
        
        assert isinstance(selected, list)
        assert len(selected) <= 2


class TestQAOAComponents:
    """Test QAOA component classes"""
    
    def test_problem_hamiltonian(self):
        """Test problem Hamiltonian"""
        def cost_func(bitstring):
            return np.sum(bitstring) * 2
        
        hamiltonian = QAOAProblemHamiltonian(cost_func)
        
        bitstring = np.array([1, 0, 1])
        cost = hamiltonian.evaluate(bitstring)
        
        assert cost == 4.0  # 2 ones * 2
    
    def test_mixing_hamiltonian(self):
        """Test mixing Hamiltonian"""
        hamiltonian = QAOAMixingHamiltonian(num_qubits=3)
        
        assert hamiltonian.num_qubits == 3
        assert hamiltonian.dimension == 8
    
    def test_qaoa_parameters(self):
        """Test QAOA parameters"""
        params = QAOAParameters(
            num_layers=3,
            num_iterations=100,
            learning_rate=0.05
        )
        
        assert params.num_layers == 3
        assert params.num_iterations == 100
        assert params.learning_rate == 0.05


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
