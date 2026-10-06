import torch
from torch import nn
from torchvision.models import maxvit_t, MaxVit_T_Weights


# ==========================================================
#  BackBone
# ==========================================================
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        BackBone = maxvit_t(weights=MaxVit_T_Weights.IMAGENET1K_V1)
        add_block = []
        add_block += [nn.Linear(1000, 1)]  # 在maxvit的基础上再加一层全连接层，因为一共有3类，所以输出为3
        add_block = nn.Sequential(*add_block)
        self.BackBone = BackBone
        self.add_block = add_block

    def forward(self, x):
        x = self.BackBone(x)
        x = self.add_block(x)
        return x


# ==========================================================
#  Gated Fusion Layer
# ==========================================================
class GatedFusion(nn.Module):
    def __init__(self, dim_img, dim_num, hidden_dim=512):
        super().__init__()
        self.dim_img = dim_img
        self.dim_num = dim_num

        self.fc_img = nn.Linear(dim_img, hidden_dim)
        self.fc_num = nn.Linear(dim_num, hidden_dim)

        self.gate = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Sigmoid()
        )

        self.fc_out = nn.Sequential(
            nn.Linear(hidden_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 1)
        )

    def forward(self, img_feat, num_feat):
        img_emb = self.fc_img(img_feat)
        num_emb = self.fc_num(num_feat)

        combined = torch.cat([img_emb, num_emb], dim=1)
        gate = self.gate(combined)

        fused = gate * img_emb + (1 - gate) * num_emb

        out = self.fc_out(fused)
        return out


# ==========================================================
#  MultiModalNet
# ==========================================================
class MultiModalNet(nn.Module):
    def __init__(self):
        super().__init__()

        # -----------------------------
        # backbone
        # -----------------------------
        self.backbone = Net().BackBone

        # 冻结 backbone
        for p in self.backbone.parameters():
            p.requires_grad = False

        # -----------------------------
        # fusion
        # image 1000 + numeric 1
        # -----------------------------
        self.gated_fusion = GatedFusion(dim_img=1000, dim_num=1, hidden_dim=512)

    def forward(self, img, num_feat):
        img_feat = self.backbone(img)
        out = self.gated_fusion(img_feat, num_feat)
        return out.squeeze(1)
