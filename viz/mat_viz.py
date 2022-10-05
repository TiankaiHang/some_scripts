import matplotlib.pyplot as plt


def simple_mat_viz(mat, save_fn="test.png"):
    r"""
    visualize the matrix
    """
    plt.matshow(mat)
    h, w = mat.shape

    for ii in range(h): plt.axhline(ii+0.5, color='k', linestyle='-')
    for ii in range(w): plt.axvline(ii+0.5, color='k', linestyle='-')

    plt.savefig(save_fn)


if __name__ == '__main__':
    import torch
    attn_matrix = torch.ones(4, 4)
    attn_matrix = torch.triu(attn_matrix)

    simple_mat_viz(1 - attn_matrix)