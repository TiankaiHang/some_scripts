# install miniconda
mkdir software
cd software
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# install cuda-11.3
# or visit ``https://developer.nvidia.com/cuda-toolkit-archive'' to find specific version
wget https://developer.download.nvidia.com/compute/cuda/11.3.0/local_installers/cuda_11.3.0_465.19.01_linux.run
sudo sh cuda_11.3.0_465.19.01_linux.run
# then run ``ls /usr/local'' to find the path to cuda
# then run ``PATH=/usr/local/cuda-11.3/bin/:$PATH'' to add it in the environment

# install pytorch
# or visit ``https://download.pytorch.org/whl/torch_stable.html'' to find specific version
# e.g., pip install torch==1.10.1+cu111 torchvision==0.11.2+cu111 torchaudio==0.10.1 -f https://download.pytorch.org/whl/torch_stable.html
conda create -n tiankai python=3.8 -y
conda activate tiankai
pip install opencv-python numpy matplotlib
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113

# install azcopy
wget https://aka.ms/downloadazcopy-v10-linux --no-check-certificate -O azcopy.tar
mkdir azcopy10 
tar -xvf azcopy.tar -C azcopy10/
sudo cp azcopy10/*/azcopy /usr/bin/
azcopy --version

# set git config
git config --global user.name "TiankaiHang"
git config --global user.email "seuhtk98@gmail.com"

# install rar
wget https://www.rarlab.com/rar/rarlinux-x64-611.tar.gz
tar -xzpvf rarlinux-x64-611.tar.gz
cd rar/
sudo make

# install ipython
conda install -c anaconda ipython
