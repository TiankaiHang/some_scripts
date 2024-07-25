import os
import torch
from tqdm.auto import tqdm
import pickle
import torch.distributed as dist


def dist_init():
    if 'MASTER_ADDR' not in os.environ:
        os.environ['MASTER_ADDR'] = 'localhost'
    if 'MASTER_PORT' not in os.environ:
        os.environ['MASTER_PORT'] = '29500'
    if 'RANK' not in os.environ:
        os.environ['RANK'] = '0'
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = '0'
    if 'WORLD_SIZE' not in os.environ:
        os.environ['WORLD_SIZE'] = '1'

    backend = 'gloo' if os.name == 'nt' else 'nccl'
    torch.distributed.init_process_group(backend=backend, init_method='env://')
    torch.cuda.set_device(int(os.environ.get('LOCAL_RANK', '0')))


def get_world_size():
    return torch.distributed.get_world_size() if torch.distributed.is_initialized() else 1


def get_rank():
    return torch.distributed.get_rank() if torch.distributed.is_initialized() else 0


def print0(*args, **kwargs):
    if get_rank() == 0:
        print(*args, **kwargs)


def flatten_part(dict_of_tensor):
    keys = list(dict_of_tensor.keys())
    shapes = []
    tensor_list = []
    for key in keys:
        shape = dict_of_tensor[key].size()
        shapes.append(shape)
        tensor_list.append(dict_of_tensor[key].view(-1))
    return keys, shapes, torch.cat(tensor_list, dim=0)


def debug_tensor(tensor):
    print0(f"---------------------------------------------")
    print0(tensor.shape)
    print0(f"---------------------------------------------")


def unflatten_part(keys, shapes, tensor):
    result = {}
    start = 0
    for i, key in enumerate(keys):
        end = start + shapes[i][0] * int(torch.prod(torch.tensor(shapes[i][1:])))
        result[key] = tensor[start:end].view(shapes[i])
        start = end
    return result


def all_gather(data):
    """
    Run all_gather on arbitrary picklable data (not necessarily tensors)
    Args:
        data: any picklable object
    Returns:
        list[data]: list of data gathered from each rank
    """
    world_size = get_world_size()
    if world_size == 1:
        return [data]

    if isinstance(data, dict):
        keys, shapes, tensor = flatten_part(data)
        keys_list   = all_gather(keys)
        shapes_list = all_gather(shapes)
        tensor_list = all_gather(tensor)
        keys   = merge_list_of_list(keys_list)
        shapes = merge_list_of_list(shapes_list)
        result = unflatten_part(keys, shapes, torch.cat(tensor_list, dim=0))
        return result

    # serialized to a Tensor
    origin_size = None
    if not isinstance(data, torch.Tensor):
        buffer = pickle.dumps(data)
        storage = torch.ByteStorage.from_buffer(buffer)
        tensor = torch.ByteTensor(storage).to("cuda")
    else:
        origin_size = data.size()
        tensor = data.reshape(-1)

    tensor_type = tensor.dtype

    # obtain Tensor size of each rank
    local_size = torch.LongTensor([tensor.numel()]).to("cuda")
    size_list = [torch.LongTensor([0]).to("cuda") for _ in range(world_size)]
    dist.all_gather(size_list, local_size)
    size_list = [int(size.item()) for size in size_list]
    max_size = max(size_list)

    # receiving Tensor from all ranks
    # we pad the tensor because torch all_gather does not support
    # gathering tensors of different shapes
    tensor_list = []
    for _ in size_list:
        tensor_list.append(torch.FloatTensor(size=(max_size,)).cuda().to(tensor_type))
    if local_size != max_size:
        padding = torch.FloatTensor(size=(max_size - local_size,)).cuda().to(tensor_type)
        tensor = torch.cat((tensor, padding), dim=0)
    dist.all_gather(tensor_list, tensor)

    data_list = []
    for size, tensor in zip(size_list, tensor_list):
        if origin_size is None:
            buffer = tensor.cpu().numpy().tobytes()[:size]
            data_list.append(pickle.loads(buffer))
        else:
            buffer = tensor[:size]
            data_list.append(buffer)

    if origin_size is not None:
        new_shape = [-1] + list(origin_size[1:])
        resized_list = []
        for data in data_list:
            # suppose the difference of tensor size exist in first dimension
            data = data.reshape(new_shape)
            resized_list.append(data)

        return resized_list
    else:
        return data_list
    

def merge_list_of_list(list_of_list):
    ret = []
    for l in list_of_list:
        ret.extend(l)
    return ret


def merge_list_of_dict(list_of_dict):
    ret = {}
    for d in list_of_dict:
        ret.update(d)
    return ret


def merge_results(results):
    if isinstance(results[0], dict):
        return merge_list_of_dict(results)
    elif isinstance(results[0], list):
        return merge_list_of_list(results)
    else:
        raise NotImplementedError


def main_worker(sub_ids):
    for _ in tqdm(range(len(sub_ids)), disable=get_rank() > 0):
        pass

    # return sub_ids
    return {i: i for i in sub_ids}


def main():
    # torch.multiprocessing.set_start_method('spawn')
    dist_init()

    # all_ids = list(range(100))
    # sub_ids = all_ids[get_rank()::get_world_size()]
    # ret = main_worker(sub_ids)
    # ret = all_gather(ret)
    # print0(merge_results(ret))
    
    torch.random.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    dict_of_tensor = {
        f"gpu-{get_rank()}-0": torch.rand(1 + get_rank(), 2 + get_rank()).cuda(),
        f"gpu-{get_rank()}-1": torch.rand(2 + get_rank(), 1 + get_rank()).cuda(),
    }
    if get_rank() == 2:
        print(f"\n\n{get_rank()} | {dict_of_tensor}")
    ret = all_gather(dict_of_tensor)
    if get_rank() == 2:
        print(f"\n\n{get_rank()} | {ret}")
    

if __name__ == "__main__":
    main()
