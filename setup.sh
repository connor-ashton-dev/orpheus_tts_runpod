#!/bin/bash

# Clone the CSM streaming repository
git clone https://github.com/davidbrowne17/csm-streaming.git temp_csm

# Copy necessary files
cp temp_csm/generator.py .
cp temp_csm/models.py .
cp temp_csm/config.py .

# Clean up
rm -rf temp_csm

# Install additional requirements
pip install -r requirements.txt 