import torch
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


# ==========================================================
#  MultiViewNet（迁移学习版）
# ==========================================================
class MultiViewNet(nn.Module):
    def __init__(self):
        super().__init__()

        # ========== backbone ==========
        self.front_backbone = Net().BackBone
        self.side_backbone = Net().BackBone
        for p in self.front_backbone.parameters():
            p.requires_grad = False

        for p in self.side_backbone.parameters():
            p.requires_grad = False

        # ========== 升级融合层 ==========
        self.fc = nn.Sequential(
            nn.Linear(2000, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(1024, 512),
            nn.ReLU(),

            nn.Linear(512, 1)
        )

    def forward(self, front_img, side_img):
        f1 = self.front_backbone(front_img)
        f2 = self.side_backbone(side_img)

        x = torch.cat([f1, f2], dim=1)
        return self.fc(x)
