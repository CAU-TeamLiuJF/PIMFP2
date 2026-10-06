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
        add_block += [nn.Linear(1000, 1)]
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

        # gate
        self.gate = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Sigmoid()
        )

        # output
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
        self.front_backbone = Net().BackBone
        self.side_backbone = Net().BackBone
        for p in self.front_backbone.parameters():
            p.requires_grad = False
        for p in self.side_backbone.parameters():
            p.requires_grad = False

        # -----------------------------
        # Gated Fusion
        # backbone 输出 1000 + 1000
        # 数值特征 3
        # -----------------------------
        self.gated_fusion = GatedFusion(dim_img=2000, dim_num=3, hidden_dim=512)

    def forward(self, front_img, side_img, num_feat):
        f1 = self.front_backbone(front_img)
        f2 = self.side_backbone(side_img)

        img_feat = torch.cat([f1, f2], dim=1)
        out = self.gated_fusion(img_feat, num_feat)
        return out.squeeze(1)
