DATA_DIR=$1

# change the default docker pytorch/pytorch to your own.

if [ -z $CUDA_VISIBLE_DEVICES ]; then
   CUDA_VISIBLE_DEVICES='all'
fi
docker run --gpus '"'device=$CUDA_VISIBLE_DEVICES'"' --ipc=host --rm -it \
   --mount src=/,dst=/home,type=bind \
   -e NVIDIA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES \
   -w /home pytorch/pytorch \
   bash -c "bash"
