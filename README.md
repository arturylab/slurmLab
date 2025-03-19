# slurmLab

slurmLab is a Python-based GUI application designed to manage and monitor SLURM jobs through an SSH connection. It provides an intuitive interface to execute common SLURM commands and view results in a formatted way.

## Features

- SSH connection management
- Job monitoring and management
- Support for common SLURM commands:
  - squeue
  - squeue -u
  - scancel
  - sinfo
- Formatted output in HTML tables
- Copy, select all and clear functionality
- Help documentation

## Requirements

- Python 3.6+
- PyQt5
- paramiko
- pathlib

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/arturylab/slurmLab.git
