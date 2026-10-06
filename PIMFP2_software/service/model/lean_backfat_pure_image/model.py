import torchvision
from torch import nn
from torchvision.models import ResNet50_Weights


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        add_block = []
        add_block += [nn.Linear(1000, 1)]
        add_block = nn.Sequential(*add_block)
        self.BackBone = torchvision.models.__dict__['resnet50'](weights=ResNet50_Weights.DEFAULT)
        self.add_block = add_block

    def forward(self, x):
        x = self.BackBone(x)
        x = self.add_block(x)
        return x
