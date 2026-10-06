from torch import nn
from torchvision.models import maxvit_t, MaxVit_T_Weights


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        BackBone = maxvit_t(weights=MaxVit_T_Weights.IMAGENET1K_V1)
        add_block = []
        add_block += [nn.Linear(1000, 1)]
        add_block = nn.Sequential(*add_block)
        self.BackBone = BackBone
        self.add_block = add_block

    def forward(self, x):
        x = self.BackBone(x)
        x = self.add_block(x)
        return x
