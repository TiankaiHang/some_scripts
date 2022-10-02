# install miniconda
mkdir software
cd software
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# install cuda-11.3
wget https://developer.download.nvidia.com/compute/cuda/11.3.0/local_installers/cuda_11.3.0_465.19.01_linux.run
sudo sh cuda_11.3.0_465.19.01_linux.run

# install pytorch
conda create -n tiankai python=3.8 -y
conda activate tiankai
pip install opencv-python numpy matplotlib
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113

# set git config
git config --global user.name "TiankaiHang"
git config --global user.email "seuhtk98@gmail.com"

# install rar
wget https://www.rarlab.com/rar/rarlinux-x64-611.tar.gz
tar -xzpvf rarlinux-x64-611.tar.gz
cd rar/
sudo make
