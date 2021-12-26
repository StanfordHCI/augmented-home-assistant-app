import numpy as np
import config
import open3d
import torch
import time


class Model(torch.nn.Module):
    def __init__(self, sensors, chunks, vector_dims):
        super().__init__()
        self.linear = torch.nn.Sequential(
            torch.nn.Linear(sensors, chunks * vector_dims),
            torch.nn.ReLU(),
        )

    def forward(self, input):
        output = self.linear(input)
        return output


vector_dims = 2
dataset_name = "models"
train_data = torch.load(dataset_name + '/train.pth')
eval_data = torch.load(dataset_name + '/eval.pth')
ckpt = torch.load(dataset_name + '/model-new-8-sensors-keyframes-3000-adam-lr-4-l2-3-not-0-1.pth')

vecs = np.array([data[1].tolist() for data in train_data])
vecs = vecs.reshape(vecs.shape[0], -1, vector_dims).transpose(1, 0, 2)
n_sensors = train_data[0][0].shape[0]
n_chunks = train_data[0][1].shape[0] // vector_dims
model = Model(n_sensors, n_chunks, vector_dims)
model.load_state_dict(ckpt)
model.eval()


def remove_ceiling(pcloud):
    no_ceiling = open3d.geometry.AxisAlignedBoundingBox(
        np.array(pcloud.get_min_bound()),
        np.array([pcloud.get_max_bound()[0], pcloud.get_max_bound()[1] - 1e-1, pcloud.get_max_bound()[2]])
    )
    return pcloud.crop(no_ceiling)


def render_home(sensors):
    sensors = torch.tensor(sensors, dtype=torch.float32)
    pred_vecs = model(sensors).detach().numpy().reshape(-1, config.vector_dims)
    pcd_combined = open3d.geometry.PointCloud()
    assemble_start = time.time()
    for chunk_id, (vec, pred_vec) in enumerate(zip(vecs, pred_vecs)):
        # find closest distance (most matching frame) from database
        frame_id = np.argmin(np.linalg.norm(vec - pred_vec, axis=1))
        pcd = open3d.io.read_point_cloud("chunks-ply/{}-{}.ply".format(frame_id, chunk_id))
        pcd_combined += pcd
    assemble_end = time.time()
    print(assemble_end - assemble_start)
    # return remove_ceiling(pcd_combined)
    return pcd_combined
