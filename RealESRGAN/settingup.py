import sys

import torchvision.transforms.functional as F
import types

patched_module = types.ModuleType("functional_tensor")

patched_module.rgb_to_grayscale = F.rgb_to_grayscale


sys.modules["torchvision.transforms.functional_tensor"] = patched_module
