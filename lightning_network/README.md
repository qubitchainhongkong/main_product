# Lightning Network Route Optimization Using Quantum Annealing

Implementation of Lightning Network transaction routing optimization using quantum annealing (Fixstars Amplify).

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-6%2F6%20passing-brightgreen.svg)]()

## 📖 Overview

This project implements the research published in the 2018 Mitou Target Program: "Development of Blockchain Acceleration Technology Using Annealing."

It realizes efficient route selection for Lightning Network (LN) transaction routing problems using quantum annealing machines.

### Background

In the Lightning Network, an off-chain technology designed to solve Bitcoin's scalability problem, transaction routing is a critical challenge. This implementation selects optimal routes while satisfying the following constraints:

1. **Capacity Constraint**: Transactions cannot pass through channels exceeding their capacity
2. **Route Constraint**: Each transaction selects only one route
3. **Distance Minimization**: Minimize route distance (number of hops) to minimize fees

## 🌟 Key Features

- **Graph Generation**: Generate scale-free networks that simulate Lightning Network topology
- **Route Finding**: Generate candidate routes using Dijkstra's algorithm
- **Hamiltonian Formulation**: Build objective functions for quantum annealing
- **Optimization Execution**: Route optimization using Fixstars Amplify AE
- **Detailed Visualization**: Statistical information and analysis of results

## 🚀 Quick Start

### Requirements

- Python 3.8 or higher
- pip
- Fixstars Amplify account (API token)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/lightning-network-routing.git
cd lightning-network-routing/lightning_network

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### API Token Configuration

1. Create an account at [Fixstars Amplify](https://amplify.fixstars.com/)
2. Obtain your API token
3. Create a `.env` file in the project root
4. Add the following content:

```bash
AMPLIFY_TOKEN=your_api_token_here
```

### Basic Usage

```bash
# Run basic example
python examples/basic_example.py

# Run full paper replication (large scale)
python examples/paper_replication.py
```

### Python Code Example

```python
from src.graph_generator import LightningNetworkGraph
from src.route_finder import RouteFinder
from src.optimizer import RouteOptimizer

# Generate graph
ln_graph = LightningNetworkGraph(
    num_nodes=100,
    num_channels=500,
    capacity_range=(200, 900)
)
graph = ln_graph.generate()

# Generate transactions
route_finder = RouteFinder(graph, num_route_candidates=3)
transactions = route_finder.generate_transactions(num_transactions=4)

# Run optimization
optimizer = RouteOptimizer(ln_graph, use_cloud_solver=True)
result = optimizer.optimize(transactions)

# Display results
optimizer.print_result(result, transactions)
```

## 📊 Paper Experimental Settings

The settings used in the original paper:

| Parameter | Value |
|-----------|-------|
| Number of Nodes | 2,000 |
| Number of Channels | 20,000 |
| Channels per Node | ~15-30 |
| Channel Capacity Range | 200-900 |
| Number of Transactions | 4 |
| Transaction Amount Range | 200-600 |
| Candidate Routes | 3 |
| α (Route Constraint Weight) | 2 |
| β (Distance Cost Weight) | (avg amount)² × 100 |
| Execution Time | 10 seconds |
| Bits Used | 361 bits |

Run `examples/paper_replication.py` to fully replicate these settings.

## 🏗️ Project Structure

```
lightning_network/
├── src/
│   ├── __init__.py
│   ├── graph_generator.py      # Graph generation
│   ├── route_finder.py         # Route finding
│   ├── hamiltonian.py          # Hamiltonian formulation
│   └── optimizer.py            # Optimization execution
├── tests/
│   ├── test_graph_generator.py
│   └── test_route_finder.py
├── examples/
│   ├── basic_example.py        # Basic example
│   └── paper_replication.py    # Paper replication
├── docs/
│   └── paper_summary.md        # Paper summary (Japanese)
├── requirements.txt
└── README.md
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html
```

## 📈 Example Results

```
======================================================================
Optimization Results
======================================================================

Execution time: 8.45s
Objective value: 125.34
Feasibility: ✓ All constraints satisfied

Statistics:
  Selected routes: 4
  Total hops: 18
  Average hops: 4.50
  Total fees: 0.8234
  Average fee: 0.2059

Selected Routes:
  Transaction 0 (8 -> 77, 375):
    Route candidate 0: 8 -> 45 -> 23 -> 77
    Hops: 3
  ...
```

## 🔬 Technical Details

### Hamiltonian Formulation

This implementation combines three Hamiltonians:

1. **Capacity Cost** (H_capacity):
   - Represents channel capacity constraints
   - Penalty: (usage - capacity)²

2. **Route Constraint** (H_route):
   - Each transaction selects only one route
   - Constraint: Σ_j x[i][j] = 1

3. **Distance Cost** (H_distance):
   - Minimize route distance (number of hops)
   - Contributes to fee minimization

**Total Hamiltonian**:
```
H_total = H_capacity + α × H_route + β × H_distance
```

### Algorithm Flow

1. **Graph Generation**: Generate scale-free network using Barabási-Albert model
2. **Candidate Route Generation**: Generate 3 candidate routes per transaction using Dijkstra's algorithm
3. **Hamiltonian Construction**: Formulate constraints and objective function for quantum annealing
4. **Optimization Execution**: Search for optimal solution using Fixstars Amplify AE
5. **Result Analysis**: Verify constraint satisfaction and statistical information

## 📚 References

- [Lightning Network Official Website](https://lightning.network/)
- [Fixstars Amplify Documentation](https://amplify.fixstars.com/docs/)
- 2018 Mitou Target Program: "Development of Blockchain Acceleration Technology Using Annealing"

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Authors

This project was developed as an implementation of academic research.

## 🙏 Acknowledgments

- Authors of the original paper from the Mitou Target Program
- Fixstars Amplify team
- Lightning Network development community

## 📮 Contact

For questions or feedback, please use GitHub issues.

---

**Note**: This project is an implementation of academic research and does not guarantee suitability for use in actual Lightning Network deployments.
