# 一些常用命令

> 安装Anaconda

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

```

> 安装cuda-11.3
```bash
# 或者访问 https://developer.nvidia.com/cuda-toolkit-archive 查找对应的版本
wget https://developer.download.nvidia.com/compute/cuda/11.3.0/local_installers/cuda_11.3.0_465.19.01_linux.run
sudo sh cuda_11.3.0_465.19.01_linux.run
```
安装完之后`nvcc -V` 看是不是预期版本。
有可能需要手动添加路径
```bash

# 看一下都有哪些cuda版本
ls /usr/local

# 然后把对应的添加到环境变量
PATH=/usr/local/cuda-11.3/bin/:$PATH

```

> PyTorch 安装
```bash
# 先创建一个环境
conda create -n torch python=3.8 -y
conda activate torch
pip install opencv-python numpy matplotlib
# 默认安装最新的
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113

# 或者访问 ``https://download.pytorch.org/whl/torch_stable.html'' 找到特定的版本，例如
pip install torch==1.10.1+cu111 torchvision==0.11.2+cu111 torchaudio==0.10.1 -f https://download.pytorch.org/whl/torch_stable.html

```

> git初始化config

```bash
git config --global user.name "YOUR_USE_NAME"
git config --global user.email "YOUR_EMAIL"
```

> 安装rar(有些包可能需要)
```
wget https://www.rarlab.com/rar/rarlinux-x64-611.tar.gz
tar -xzpvf rarlinux-x64-611.tar.gz
cd rar/
sudo make
```

> git 撤销 commit 操作
```bash
git add .
git commit -m "up"
# 之后想撤销commit
git reset --soft HEAD^

# 如果两次commit都想撤回
git reset --soft HEAD~2

# 不删除工作空间改动代码，撤销commit，并且撤销 git add . 操作
git reset --mixed HEAD^

# 不删除工作空间改动代码，撤销commit，不撤销git add .
git reset --soft HEAD^

# 删除工作空间改动代码，撤销commit，撤销git add .
git reset --hard HEAD^

# 只是想修改注释
git commit --amend
```