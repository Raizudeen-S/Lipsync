#!/bin/bash
 
# Make the script executable with: chmod +x install_mmlab.sh
# Execute the script with: ./install_mmlab.sh
 
echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt || { echo "Failed to install requirements.txt"; exit 1; }
 
echo "Installing mmlab packages..."
# Update openmim and install mmengine
pip install --no-cache-dir -U openmim || { echo "Failed to install openmim"; exit 1; }
mim install mmengine || { echo "Failed to install mmengine"; exit 1; }
 
# Install specific versions of mmlab components
mim install "mmcv==2.0.1" || { echo "Failed to install mmcv==2.0.1"; exit 1; }
mim install "mmdet==3.1.0" || { echo "Failed to install mmdet==3.1.0"; exit 1; }
mim install "mmpose==1.1.0" || { echo "Failed to install mmpose==1.1.0"; exit 1; }
 
# Execute python setup1.py if it exists
if [ -f "setupmodel.py" ]; then
    echo "Running setup1.py..."
    python setupmodel.py || { echo "Failed to run setupmodel.py"; exit 1; }
else
    echo "setupmodel.py not found, skipping this step."
fi
 
echo "Installation completed successfully!"